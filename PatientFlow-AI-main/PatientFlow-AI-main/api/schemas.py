"""Pydantic schemas for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --------------------------- reference ---------------------------
class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    specialty: str
    mean_service_min: float
    clinic_id: Optional[int] = None


class AppointmentTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    no_show_base: float
    default_price: float = 0.0


class ClinicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    city: str
    phone: Optional[str] = None
    created_at: datetime


class ClinicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    city: str = Field(..., min_length=1, max_length=80)
    phone: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    full_name: str = Field(..., min_length=1, max_length=120)
    role: str = Field("staff", pattern="^(admin|doctor|staff)$")
    password: str = Field(..., min_length=4, max_length=128)


# --------------------------- visit notes / invoices ---------------
class VisitNoteBase(BaseModel):
    chief_complaint: str = Field(..., min_length=1, max_length=255)
    diagnosis: Optional[str] = Field(None, max_length=255)
    prescription: Optional[str] = None
    follow_up_days: Optional[int] = Field(None, ge=0, le=365)


class VisitNoteCreate(VisitNoteBase):
    appointment_id: int


class VisitNoteOut(VisitNoteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: int
    created_at: datetime


class InvoiceBase(BaseModel):
    amount: float = Field(..., ge=0)
    currency: str = Field("INR", min_length=3, max_length=3)
    status: str = Field("pending", pattern="^(pending|paid|refunded|void)$")


class InvoiceCreate(InvoiceBase):
    appointment_id: int


class InvoiceUpdate(BaseModel):
    amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(pending|paid|refunded|void)$")


class InvoiceOut(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: int
    issued_at: datetime
    paid_at: Optional[datetime] = None


# --------------------------- stats -------------------------------
class StatusCount(BaseModel):
    status: str
    count: int


class DoctorLoad(BaseModel):
    doctor_id: str
    specialty: str
    total: int
    completed: int
    cancelled: int
    no_show: int


class RevenueByType(BaseModel):
    appointment_type_id: str
    invoices: int
    total_amount: float


class StatsResponse(BaseModel):
    totals: dict
    appointments_by_status: list[StatusCount]
    doctor_load: list[DoctorLoad]
    revenue_by_type: list[RevenueByType]
    top_no_show_patients: list[dict]


# --------------------------- patients ----------------------------
class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^[MFO]$")
    email: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    has_insurance: bool = True
    prior_visits: int = Field(0, ge=0)
    prior_no_shows: int = Field(0, ge=0)
    sms_reminder: bool = True


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[str] = Field(None, pattern="^[MFO]$")
    email: Optional[str] = None
    phone: Optional[str] = None
    has_insurance: Optional[bool] = None
    prior_visits: Optional[int] = Field(None, ge=0)
    prior_no_shows: Optional[int] = Field(None, ge=0)
    sms_reminder: Optional[bool] = None


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --------------------------- appointments ------------------------
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: str
    appointment_type_id: str
    appointment_time: datetime
    lead_time_days: int = Field(0, ge=0)
    status: str = Field("scheduled", pattern="^(scheduled|completed|cancelled|no_show)$")
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[str] = None
    appointment_type_id: Optional[str] = None
    appointment_time: Optional[datetime] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|no_show)$")
    notes: Optional[str] = None


class AppointmentOut(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --------------------------- predictions -------------------------
class PatientPayload(BaseModel):
    """Ephemeral prediction input (matches ML feature contract)."""

    doctor_id: str
    appointment_type: str
    appointment_time: datetime
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^[MFO]$")
    has_insurance: bool
    lead_time_days: int = Field(..., ge=0)
    prior_no_shows: int = Field(..., ge=0)
    prior_visits: int = Field(..., ge=0)
    sms_reminder: bool


class WaitOut(BaseModel):
    p10: float
    p50: float
    p90: float


class PredictRequest(BaseModel):
    payload: PatientPayload
    patient_id: Optional[int] = None
    appointment_id: Optional[int] = None
    persist: bool = True


class PredictResponse(BaseModel):
    id: Optional[int] = None
    cancellation_prob: float
    cancellation_threshold: float
    cancellation_flag: bool
    expected_wait_minutes: WaitOut
    interpretation: str


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: Optional[int]
    patient_id: Optional[int]
    cancellation_prob: float
    cancellation_flag: bool
    wait_p10: float
    wait_p50: float
    wait_p90: float
    interpretation: str
    created_at: datetime


# --------------------------- recommendations ---------------------
class RecommendRequest(BaseModel):
    patient: PatientPayload
    patient_id: Optional[int] = None
    candidate_doctors: Optional[list[str]] = None
    horizon_hours: int = Field(48, ge=1, le=336)
    step_minutes: int = Field(60, ge=15, le=240)
    top_k: int = Field(5, ge=1, le=20)
    persist: bool = True


class SlotOut(BaseModel):
    appointment_time: datetime
    doctor_id: str
    expected_wait: WaitOut
    cancellation_prob: float
    score: float
    rationale: str


class RecommendResponse(BaseModel):
    run_id: Optional[int] = None
    recommendations: list[SlotOut]
