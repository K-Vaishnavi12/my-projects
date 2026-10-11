"""
SQLAlchemy ORM models for PatientFlow AI (SQL-first architecture).

Schema (12 tables):

Reference / auth
    clinics              - clinic locations
    users                - staff accounts (username, role, hashed password)
    doctors              - clinicians (FK -> clinics)
    appointment_types    - service catalog

Operational
    patients             - patient records
    appointments         - scheduled visits (FK -> patient, doctor, type)
    visit_notes          - clinical notes per completed appointment
    invoices             - billing per appointment

ML + audit
    predictions          - one row per /predict call
    recommendation_runs  - one row per /recommend request
    recommended_slots    - child rows of recommendation_runs
    audit_log            - every mutating request (create/update/delete)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# --------------------------- reference / auth ---------------------------
class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="clinic")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="staff"
    )  # admin | doctor | staff
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    specialty: Mapped[str] = mapped_column(String(64), nullable=False)
    mean_service_min: Mapped[float] = mapped_column(Float, nullable=False)
    clinic_id: Mapped[int | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True, index=True
    )

    clinic: Mapped[Clinic | None] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")


class AppointmentType(Base):
    __tablename__ = "appointment_types"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    no_show_base: Mapped[float] = mapped_column(Float, nullable=False)
    default_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="appt_type")


# --------------------------- operational --------------------------------
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    has_insurance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prior_visits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prior_no_shows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sms_reminder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[str] = mapped_column(
        ForeignKey("doctors.id"), nullable=False, index=True
    )
    appointment_type_id: Mapped[str] = mapped_column(
        ForeignKey("appointment_types.id"), nullable=False
    )
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="scheduled", nullable=False, index=True
    )  # scheduled | completed | cancelled | no_show
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    patient: Mapped[Patient] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")
    appt_type: Mapped[AppointmentType] = relationship(back_populates="appointments")
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )
    visit_note: Mapped["VisitNote | None"] = relationship(
        back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )
    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )


class VisitNote(Base):
    __tablename__ = "visit_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    chief_complaint: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    appointment: Mapped[Appointment] = relationship(back_populates="visit_note")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )  # pending | paid | refunded | void
    issued_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    appointment: Mapped[Appointment] = relationship(back_populates="invoice")


# --------------------------- ML + audit ---------------------------------
class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    cancellation_prob: Mapped[float] = mapped_column(Float, nullable=False)
    cancellation_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    cancellation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    wait_p10: Mapped[float] = mapped_column(Float, nullable=False)
    wait_p50: Mapped[float] = mapped_column(Float, nullable=False)
    wait_p90: Mapped[float] = mapped_column(Float, nullable=False)
    interpretation: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    appointment: Mapped[Appointment | None] = relationship(back_populates="predictions")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    step_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    slots: Mapped[list["RecommendedSlot"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RecommendedSlot(Base):
    __tablename__ = "recommended_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancellation_prob: Mapped[float] = mapped_column(Float, nullable=False)
    wait_p10: Mapped[float] = mapped_column(Float, nullable=False)
    wait_p50: Mapped[float] = mapped_column(Float, nullable=False)
    wait_p90: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(String(255), nullable=False)

    run: Mapped[RecommendationRun] = relationship(back_populates="slots")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # create|update|delete
    diff_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )
