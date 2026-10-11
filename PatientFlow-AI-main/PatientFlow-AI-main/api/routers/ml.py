"""Prediction + recommendation endpoints. Every call is persisted to SQL."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml" / "src"))

from inference import PatientFlowModel, default_candidate_times  # noqa: E402
from generate_data import APPT_TYPES, DOCTORS  # noqa: E402

from ..db import get_db
from ..models import (
    Appointment,
    Patient,
    Prediction,
    RecommendationRun,
    RecommendedSlot,
)
from ..schemas import (
    PredictionOut,
    PredictRequest,
    PredictResponse,
    RecommendRequest,
    RecommendResponse,
    SlotOut,
    WaitOut,
)

router = APIRouter(tags=["ml"])

MODELS_DIR = ROOT / "ml" / "models"
_MODEL: Optional[PatientFlowModel] = None


def get_model() -> PatientFlowModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = PatientFlowModel(models_dir=MODELS_DIR)
    return _MODEL


def _interpret(cancel: float, wait_p10: float, wait_p90: float) -> str:
    interp: list[str] = []
    if cancel < 0.10:
        interp.append("very low cancellation risk")
    elif cancel < 0.25:
        interp.append("typical cancellation risk")
    elif cancel < 0.45:
        interp.append("elevated cancellation risk - consider reminder")
    else:
        interp.append("high cancellation risk - double-book or follow up")
    spread = wait_p90 - wait_p10
    if spread < 10:
        interp.append("wait estimate is high-confidence")
    elif spread > 25:
        interp.append("wait estimate is highly variable")
    return "; ".join(interp)


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    payload = req.payload
    raw = payload.model_dump()
    if raw["doctor_id"] not in DOCTORS:
        raise HTTPException(400, f"Unknown doctor_id '{raw['doctor_id']}'.")
    if raw["appointment_type"] not in APPT_TYPES:
        raise HTTPException(400, f"Unknown appointment_type '{raw['appointment_type']}'.")
    if req.patient_id is not None and not db.get(Patient, req.patient_id):
        raise HTTPException(400, f"Unknown patient_id {req.patient_id}")
    if req.appointment_id is not None and not db.get(Appointment, req.appointment_id):
        raise HTTPException(400, f"Unknown appointment_id {req.appointment_id}")

    model = get_model()
    cancel = float(model.predict_cancellation(raw))
    wait = model.predict_wait(raw)
    threshold = float(model.threshold)
    flag = bool(cancel >= threshold)
    interp = _interpret(cancel, wait.p10, wait.p90)

    row_id: Optional[int] = None
    if req.persist:
        row = Prediction(
            appointment_id=req.appointment_id,
            patient_id=req.patient_id,
            payload_json=json.loads(payload.model_dump_json()),
            cancellation_prob=cancel,
            cancellation_threshold=threshold,
            cancellation_flag=flag,
            wait_p10=float(wait.p10),
            wait_p50=float(wait.p50),
            wait_p90=float(wait.p90),
            interpretation=interp,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        row_id = row.id

    return PredictResponse(
        id=row_id,
        cancellation_prob=round(cancel, 4),
        cancellation_threshold=round(threshold, 4),
        cancellation_flag=flag,
        expected_wait_minutes=WaitOut(p10=wait.p10, p50=wait.p50, p90=wait.p90),
        interpretation=interp,
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    patient = req.patient.model_dump()
    if patient["doctor_id"] not in DOCTORS:
        raise HTTPException(400, f"Unknown doctor_id '{patient['doctor_id']}'.")
    if patient["appointment_type"] not in APPT_TYPES:
        raise HTTPException(400, f"Unknown appointment_type '{patient['appointment_type']}'.")

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

    recs = get_model().recommend_slots(
        patient=patient,
        candidate_times=cands,
        candidate_doctors=candidate_doctors,
        top_k=req.top_k,
    )

    run_id: Optional[int] = None
    if req.persist:
        run = RecommendationRun(
            patient_id=req.patient_id,
            payload_json=json.loads(req.patient.model_dump_json()),
            horizon_hours=req.horizon_hours,
            step_minutes=req.step_minutes,
            top_k=req.top_k,
        )
        db.add(run)
        db.flush()
        for rank, r in enumerate(recs, start=1):
            db.add(
                RecommendedSlot(
                    run_id=run.id,
                    rank=rank,
                    doctor_id=r.doctor_id,
                    appointment_time=r.appointment_time,
                    cancellation_prob=float(r.cancellation_prob),
                    wait_p10=float(r.expected_wait.p10),
                    wait_p50=float(r.expected_wait.p50),
                    wait_p90=float(r.expected_wait.p90),
                    score=float(r.score),
                    rationale=r.rationale,
                )
            )
        db.commit()
        run_id = run.id

    return RecommendResponse(
        run_id=run_id,
        recommendations=[
            SlotOut(
                appointment_time=r.appointment_time,
                doctor_id=r.doctor_id,
                expected_wait=WaitOut(
                    p10=r.expected_wait.p10,
                    p50=r.expected_wait.p50,
                    p90=r.expected_wait.p90,
                ),
                cancellation_prob=round(r.cancellation_prob, 4),
                score=round(r.score, 4),
                rationale=r.rationale,
            )
            for r in recs
        ],
    )


@router.get("/predictions", response_model=list[PredictionOut])
def list_predictions(
    patient_id: Optional[int] = None,
    appointment_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Prediction)
    if patient_id is not None:
        q = q.filter(Prediction.patient_id == patient_id)
    if appointment_id is not None:
        q = q.filter(Prediction.appointment_id == appointment_id)
    return (
        q.order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(min(limit, 500))
        .all()
    )
