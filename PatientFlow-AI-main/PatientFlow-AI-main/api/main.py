"""
PatientFlow AI - FastAPI service, now SQL-backed (MySQL/MariaDB via SQLAlchemy).

On startup:
    1. Ensures the target MySQL database exists (CREATE DATABASE IF NOT EXISTS)
    2. Creates all tables from the ORM models
    3. Seeds reference tables (doctors, appointment_types) from ml/src constants
    4. Warms up the ML model

Endpoints:
    GET    /health
    GET    /metadata
    GET    /doctors,  /appointment-types
    CRUD   /patients
    CRUD   /appointments
    POST   /predict, /recommend      (persist to SQL by default)
    GET    /predictions
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml" / "src"))

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from .db import get_db  # noqa: E402
from .models import AppointmentType, Doctor  # noqa: E402
from .routers import (  # noqa: E402
    appointments,
    invoices,
    ml,
    patients,
    reference,
    stats,
    users,
    visit_notes,
)
from .seed import init_db  # noqa: E402

REPORTS_DIR = ROOT / "ml" / "reports"


app = FastAPI(
    title="PatientFlow AI",
    description=(
        "SQL-backed ML service. Persists patients, appointments, predictions "
        "and slot recommendations to MySQL, and serves cancellation-risk / "
        "wait-time forecasts from a multi-model pipeline."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    ml.get_model()


app.include_router(reference.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(visit_notes.router)
app.include_router(invoices.router)
app.include_router(stats.router)
app.include_router(ml.router)


@app.get("/health", tags=["meta"])
def health(db: Session = Depends(get_db)) -> dict:
    # ping the DB so /health also reflects DB liveness
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "service": "PatientFlow AI", "db": db_ok}


@app.get("/metadata", tags=["meta"])
def metadata(db: Session = Depends(get_db)) -> dict:
    metrics_file = REPORTS_DIR / "metrics.json"
    metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else {}
    doctors = [
        {
            "id": d.id,
            "specialty": d.specialty,
            "mean_service_min": d.mean_service_min,
        }
        for d in db.query(Doctor).order_by(Doctor.id).all()
    ]
    appt_types = [
        {"id": t.id, "no_show_base": t.no_show_base}
        for t in db.query(AppointmentType).order_by(AppointmentType.id).all()
    ]
    return {
        "doctors": doctors,
        "appointment_types": appt_types,
        "metrics": metrics,
        "threshold": ml.get_model().threshold,
    }
