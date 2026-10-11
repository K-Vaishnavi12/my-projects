"""
PatientFlow AI - FastAPI service.

Endpoints:
    GET  /health
    GET  /metadata          - doctors, appointment types, model metrics
    POST /predict           - cancel prob + wait quantiles for one patient
    POST /recommend         - top-K slot recommendations
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Make ml/src importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml" / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from inference import (  # noqa: E402  (ml/src import after sys.path tweak)
    PatientFlowModel, default_candidate_times,
)
from generate_data import APPT_TYPES, DOCTORS  # noqa: E402

# -----------------------------------------------------------------------------
# Model load (eager, on import)
# -----------------------------------------------------------------------------
MODELS_DIR = ROOT / "ml" / "models"
REPORTS_DIR = ROOT / "ml" / "reports"

_MODEL: PatientFlowModel | None = None


def get_model() -> PatientFlowModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = PatientFlowModel(models_dir=MODELS_DIR)
    return _MODEL


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class PatientPayload(BaseModel):
    doctor_id: str = Field(..., description="Doctor identifier (see /metadata).")
    appointment_type: str = Field(..., description="One of consultation, follow_up, diagnostic, vaccination, emergency.")
    appointment_time: datetime = Field(..., description="Scheduled appointment time (ISO 8601).")
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., description="M / F / O.")
    has_insurance: bool
    lead_time_days: int = Field(..., ge=0)
    prior_no_shows: int = Field(..., ge=0)
    prior_visits: int = Field(..., ge=0)
    sms_reminder: bool


class WaitOut(BaseModel):
    p10: float
    p50: float
    p90: float


class PredictResponse(BaseModel):
    cancellation_prob: float
    cancellation_threshold: float
    cancellation_flag: bool
    expected_wait_minutes: WaitOut
    interpretation: str


class RecommendRequest(BaseModel):
    patient: PatientPayload
    candidate_doctors: Optional[list[str]] = None
    horizon_hours: int = Field(48, ge=1, le=336)
    step_minutes: int = Field(60, ge=15, le=240)
    top_k: int = Field(5, ge=1, le=20)


class SlotOut(BaseModel):
    appointment_time: datetime
    doctor_id: str
    expected_wait: WaitOut
    cancellation_prob: float
    score: float
    rationale: str


class RecommendResponse(BaseModel):
    recommendations: list[SlotOut]


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(
    title="PatientFlow AI",
    description=(
        "ML service that predicts patient cancellation probability and "
        "wait-time quantiles, and recommends optimal appointment slots."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warmup() -> None:
    get_model()


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "PatientFlow AI"}


@app.get("/metadata")
def metadata() -> dict:
    metrics_file = REPORTS_DIR / "metrics.json"
    metrics = (
        json.loads(metrics_file.read_text()) if metrics_file.exists() else {}
    )
    doctors = [
        {
            "id": did,
            "specialty": meta["specialty"],
            "mean_service_min": meta["mean_service_min"],
        }
        for did, meta in DOCTORS.items()
    ]
    appt_types = [
        {"id": t, "no_show_base": APPT_TYPES[t]["no_show_base"]}
        for t in APPT_TYPES
    ]
    return {
        "doctors": doctors,
        "appointment_types": appt_types,
        "metrics": metrics,
        "threshold": get_model().threshold,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PatientPayload) -> PredictResponse:
    model = get_model()
    raw = payload.model_dump()
    # Sanity validation against known doctors/types
    if raw["doctor_id"] not in DOCTORS:
        raise HTTPException(400, f"Unknown doctor_id '{raw['doctor_id']}'.")
    if raw["appointment_type"] not in APPT_TYPES:
        raise HTTPException(400, f"Unknown appointment_type '{raw['appointment_type']}'.")

    cancel = model.predict_cancellation(raw)
    wait = model.predict_wait(raw)
    threshold = model.threshold
    flag = bool(cancel >= threshold)

    interp = []
    if cancel < 0.10:
        interp.append("very low cancellation risk")
    elif cancel < 0.25:
        interp.append("typical cancellation risk")
    elif cancel < 0.45:
        interp.append("elevated cancellation risk - consider reminder")
    else:
        interp.append("high cancellation risk - double-book or follow up")

    spread = wait.p90 - wait.p10
    if spread < 10:
        interp.append("wait estimate is high-confidence")
    elif spread > 25:
        interp.append("wait estimate is highly variable")

    return PredictResponse(
        cancellation_prob=round(cancel, 4),
        cancellation_threshold=round(threshold, 4),
        cancellation_flag=flag,
        expected_wait_minutes=WaitOut(**wait.to_dict()),
        interpretation="; ".join(interp),
    )


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    model = get_model()
    patient = req.patient.model_dump()

    if req.candidate_doctors:
        for d in req.candidate_doctors:
            if d not in DOCTORS:
                raise HTTPException(400, f"Unknown doctor_id '{d}'.")
        candidate_doctors = req.candidate_doctors
    else:
        candidate_doctors = list(DOCTORS.keys())

    start = patient["appointment_time"]
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    cands = default_candidate_times(start, req.horizon_hours, req.step_minutes)
    if not cands:
        raise HTTPException(400, "No valid candidate slots in the requested window.")

    recs = model.recommend_slots(
        patient=patient,
        candidate_times=cands,
        candidate_doctors=candidate_doctors,
        top_k=req.top_k,
    )

    return RecommendResponse(recommendations=[
        SlotOut(
            appointment_time=r.appointment_time,
            doctor_id=r.doctor_id,
            expected_wait=WaitOut(**r.expected_wait.to_dict()),
            cancellation_prob=round(r.cancellation_prob, 4),
            score=round(r.score, 4),
            rationale=r.rationale,
        ) for r in recs
    ])
