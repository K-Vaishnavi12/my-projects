"""SQL-driven analytics. All aggregation is done in the database via GROUP BY."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Appointment, AppointmentType, Doctor, Invoice, Patient
from ..schemas import DoctorLoad, RevenueByType, StatsResponse, StatusCount

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)) -> StatsResponse:
    totals = {
        "patients": db.query(func.count(Patient.id)).scalar() or 0,
        "appointments": db.query(func.count(Appointment.id)).scalar() or 0,
        "doctors": db.query(func.count(Doctor.id)).scalar() or 0,
        "invoices": db.query(func.count(Invoice.id)).scalar() or 0,
        "revenue_paid": float(
            db.query(func.coalesce(func.sum(Invoice.amount), 0))
            .filter(Invoice.status == "paid")
            .scalar()
            or 0
        ),
        "revenue_pending": float(
            db.query(func.coalesce(func.sum(Invoice.amount), 0))
            .filter(Invoice.status == "pending")
            .scalar()
            or 0
        ),
    }

    # Appointments grouped by status
    status_rows = (
        db.query(Appointment.status, func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )
    appointments_by_status = [
        StatusCount(status=s, count=int(c)) for s, c in status_rows
    ]

    # Load per doctor (with cross-status counts)
    load_rows = (
        db.query(
            Doctor.id,
            Doctor.specialty,
            func.count(Appointment.id).label("total"),
            func.sum(case((Appointment.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((Appointment.status == "cancelled", 1), else_=0)).label("cancelled"),
            func.sum(case((Appointment.status == "no_show", 1), else_=0)).label("no_show"),
        )
        .outerjoin(Appointment, Appointment.doctor_id == Doctor.id)
        .group_by(Doctor.id, Doctor.specialty)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )
    doctor_load = [
        DoctorLoad(
            doctor_id=r[0],
            specialty=r[1],
            total=int(r[2] or 0),
            completed=int(r[3] or 0),
            cancelled=int(r[4] or 0),
            no_show=int(r[5] or 0),
        )
        for r in load_rows
    ]

    # Revenue grouped by appointment type
    rev_rows = (
        db.query(
            AppointmentType.id,
            func.count(Invoice.id).label("invoices"),
            func.coalesce(func.sum(Invoice.amount), 0).label("total_amount"),
        )
        .outerjoin(Appointment, Appointment.appointment_type_id == AppointmentType.id)
        .outerjoin(Invoice, Invoice.appointment_id == Appointment.id)
        .group_by(AppointmentType.id)
        .order_by(func.coalesce(func.sum(Invoice.amount), 0).desc())
        .all()
    )
    revenue_by_type = [
        RevenueByType(
            appointment_type_id=r[0],
            invoices=int(r[1] or 0),
            total_amount=float(r[2] or 0),
        )
        for r in rev_rows
    ]

    # Top 5 no-show patients (observed, not the priors)
    top_ns = (
        db.query(
            Patient.id,
            Patient.full_name,
            func.count(Appointment.id).label("no_shows"),
        )
        .join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.status == "no_show")
        .group_by(Patient.id, Patient.full_name)
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
        .all()
    )
    top_no_show_patients = [
        {"patient_id": int(r[0]), "full_name": r[1], "no_shows": int(r[2])}
        for r in top_ns
    ]

    return StatsResponse(
        totals=totals,
        appointments_by_status=appointments_by_status,
        doctor_load=doctor_load,
        revenue_by_type=revenue_by_type,
        top_no_show_patients=top_no_show_patients,
    )
