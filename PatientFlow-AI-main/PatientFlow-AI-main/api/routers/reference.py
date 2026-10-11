"""Reference endpoints: doctors, appointment types, clinics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..audit import audit
from ..db import get_db
from ..models import AppointmentType, Clinic, Doctor
from ..schemas import (
    AppointmentTypeOut,
    ClinicCreate,
    ClinicOut,
    DoctorOut,
)

router = APIRouter(tags=["reference"])


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db)) -> list[Doctor]:
    return db.query(Doctor).order_by(Doctor.id).all()


@router.get("/appointment-types", response_model=list[AppointmentTypeOut])
def list_appt_types(db: Session = Depends(get_db)) -> list[AppointmentType]:
    return db.query(AppointmentType).order_by(AppointmentType.id).all()


@router.get("/clinics", response_model=list[ClinicOut])
def list_clinics(db: Session = Depends(get_db)) -> list[Clinic]:
    return db.query(Clinic).order_by(Clinic.id).all()


@router.post("/clinics", response_model=ClinicOut, status_code=status.HTTP_201_CREATED)
def create_clinic(payload: ClinicCreate, db: Session = Depends(get_db)):
    c = Clinic(**payload.model_dump())
    db.add(c)
    db.flush()
    audit(db, "clinic", c.id, "create", diff=payload.model_dump())
    db.commit()
    db.refresh(c)
    return c


@router.delete("/clinics/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clinic(clinic_id: int, db: Session = Depends(get_db)):
    c = db.get(Clinic, clinic_id)
    if not c:
        raise HTTPException(404, "Clinic not found")
    audit(db, "clinic", c.id, "delete")
    db.delete(c)
    db.commit()
