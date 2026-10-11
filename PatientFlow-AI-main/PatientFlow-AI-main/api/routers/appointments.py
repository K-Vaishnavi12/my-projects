"""CRUD for appointments."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..audit import audit
from ..db import get_db
from ..models import Appointment, AppointmentType, Doctor, Patient
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _validate_fks(
    db: Session,
    patient_id: Optional[int] = None,
    doctor_id: Optional[str] = None,
    appt_type_id: Optional[str] = None,
) -> None:
    if patient_id is not None and not db.get(Patient, patient_id):
        raise HTTPException(400, f"Unknown patient_id {patient_id}")
    if doctor_id is not None and not db.get(Doctor, doctor_id):
        raise HTTPException(400, f"Unknown doctor_id '{doctor_id}'")
    if appt_type_id is not None and not db.get(AppointmentType, appt_type_id):
        raise HTTPException(400, f"Unknown appointment_type_id '{appt_type_id}'")


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    patient_id: Optional[int] = None,
    doctor_id: Optional[str] = None,
    status_: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Appointment)
    if patient_id is not None:
        q = q.filter(Appointment.patient_id == patient_id)
    if doctor_id is not None:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if status_ is not None:
        q = q.filter(Appointment.status == status_)
    return (
        q.order_by(Appointment.appointment_time.desc())
        .offset(skip)
        .limit(min(limit, 500))
        .all()
    )


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    _validate_fks(db, payload.patient_id, payload.doctor_id, payload.appointment_type_id)
    a = Appointment(**payload.model_dump())
    db.add(a)
    db.flush()
    audit(db, "appointment", a.id, "create", diff=json.loads(payload.model_dump_json()))
    db.commit()
    db.refresh(a)
    return a


@router.get("/{appt_id}", response_model=AppointmentOut)
def get_appointment(appt_id: int, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "Appointment not found")
    return a


@router.patch("/{appt_id}", response_model=AppointmentOut)
def update_appointment(
    appt_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)
):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "Appointment not found")
    data = payload.model_dump(exclude_unset=True)
    _validate_fks(
        db,
        doctor_id=data.get("doctor_id"),
        appt_type_id=data.get("appointment_type_id"),
    )
    for k, v in data.items():
        setattr(a, k, v)
    audit(
        db,
        "appointment",
        a.id,
        "update",
        diff=json.loads(payload.model_dump_json(exclude_unset=True)),
    )
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{appt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appt_id: int, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "Appointment not found")
    audit(db, "appointment", a.id, "delete")
    db.delete(a)
    db.commit()
    return None
