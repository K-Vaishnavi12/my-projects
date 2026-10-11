"""Initialise the DB, seed reference tables + sample operational data."""

from __future__ import annotations

import hashlib
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml" / "src"))

from generate_data import APPT_TYPES, DOCTORS  # noqa: E402

from .db import Base, SessionLocal, engine, ensure_database_exists  # noqa: E402
from .models import (  # noqa: E402
    Appointment,
    AppointmentType,
    Clinic,
    Doctor,
    Invoice,
    Patient,
    User,
    VisitNote,
)

# Default prices per appointment type (INR).
DEFAULT_PRICES = {
    "consultation": 500.0,
    "follow_up": 300.0,
    "diagnostic": 1500.0,
    "vaccination": 800.0,
    "emergency": 2500.0,
}


def _sha256(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def init_db() -> None:
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_reference(db)
        seed_sample_data(db)


def seed_reference(db: Session) -> None:
    """Reference tables: clinics, doctors, appointment_types, admin user."""
    changed = False

    # Clinics
    if db.query(Clinic).count() == 0:
        db.add_all(
            [
                Clinic(name="Central Health Clinic", city="Bengaluru", phone="+91-80-1234-5678"),
                Clinic(name="Northside Medical Center", city="Delhi", phone="+91-11-2345-6789"),
                Clinic(name="Harbor Family Practice", city="Mumbai", phone="+91-22-3456-7890"),
            ]
        )
        db.flush()
        changed = True

    clinic_ids = [c.id for c in db.query(Clinic).order_by(Clinic.id).all()]

    # Appointment types (with default prices)
    for tid, meta in APPT_TYPES.items():
        row = db.get(AppointmentType, tid)
        if row is None:
            db.add(
                AppointmentType(
                    id=tid,
                    no_show_base=float(meta["no_show_base"]),
                    default_price=DEFAULT_PRICES.get(tid, 500.0),
                )
            )
            changed = True

    # Doctors (round-robin clinics)
    for i, (did, meta) in enumerate(DOCTORS.items()):
        if not db.get(Doctor, did):
            db.add(
                Doctor(
                    id=did,
                    specialty=meta["specialty"],
                    mean_service_min=float(meta["mean_service_min"]),
                    clinic_id=clinic_ids[i % len(clinic_ids)] if clinic_ids else None,
                )
            )
            changed = True

    # Admin user
    if db.query(User).count() == 0:
        db.add(
            User(
                username="admin",
                full_name="System Admin",
                role="admin",
                password_hash=_sha256("admin"),
                is_active=True,
            )
        )
        db.add(
            User(
                username="reception",
                full_name="Front Desk",
                role="staff",
                password_hash=_sha256("reception"),
                is_active=True,
            )
        )
        changed = True

    if changed:
        db.commit()


SAMPLE_PATIENTS = [
    ("Aarav Sharma", 34, "M", True, 4, 0, True),
    ("Priya Iyer", 29, "F", True, 2, 1, True),
    ("Rohan Mehta", 52, "M", False, 8, 2, False),
    ("Sanya Kapoor", 41, "F", True, 6, 0, True),
    ("Devansh Rao", 8, "M", True, 3, 0, True),
    ("Meera Nair", 67, "F", True, 12, 3, False),
    ("Kabir Singh", 23, "M", False, 1, 1, True),
    ("Anaya Gupta", 45, "F", True, 5, 0, True),
]


def seed_sample_data(db: Session) -> None:
    """Populate patients + a few weeks of appointments so the DB isn't empty."""
    if db.query(Patient).count() > 0:
        return  # already seeded

    doctors = [d.id for d in db.query(Doctor).all()]
    appt_types = [t.id for t in db.query(AppointmentType).all()]
    prices = {t.id: t.default_price for t in db.query(AppointmentType).all()}
    if not doctors or not appt_types:
        return

    rng = random.Random(42)

    # Insert patients
    patients: list[Patient] = []
    for name, age, sex, ins, visits, no_shows, sms in SAMPLE_PATIENTS:
        p = Patient(
            full_name=name,
            age=age,
            sex=sex,
            email=name.lower().replace(" ", ".") + "@example.com",
            phone=f"+91-9{rng.randrange(100000000, 999999999)}",
            has_insurance=ins,
            prior_visits=visits,
            prior_no_shows=no_shows,
            sms_reminder=sms,
        )
        db.add(p)
        patients.append(p)
    db.flush()

    # Generate ~50 appointments spread across the last 30 days and next 14 days
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    statuses = ["scheduled", "completed", "cancelled", "no_show"]
    status_weights = [0.35, 0.45, 0.12, 0.08]

    for _ in range(50):
        pat = rng.choice(patients)
        doc = rng.choice(doctors)
        at = rng.choice(appt_types)
        # 60% in the past, 40% future
        offset_hours = rng.randrange(-30 * 24, 14 * 24)
        appt_time = now + timedelta(hours=offset_hours)
        lead = max(0, (appt_time - now).days) if offset_hours >= 0 else rng.randrange(0, 10)

        # Past-dated -> pick from all statuses; future -> mostly scheduled
        if offset_hours >= 0:
            status = "scheduled" if rng.random() < 0.9 else "cancelled"
        else:
            status = rng.choices(statuses, weights=status_weights, k=1)[0]

        appt = Appointment(
            patient_id=pat.id,
            doctor_id=doc,
            appointment_type_id=at,
            appointment_time=appt_time,
            lead_time_days=lead,
            status=status,
            notes=None,
        )
        db.add(appt)
        db.flush()

        # Completed visits get a note + a paid invoice
        if status == "completed":
            db.add(
                VisitNote(
                    appointment_id=appt.id,
                    chief_complaint=rng.choice(
                        ["fever", "checkup", "back pain", "cough", "headache", "follow-up"]
                    ),
                    diagnosis=rng.choice(
                        ["viral fever", "healthy", "muscle strain", "URI", "migraine", "stable"]
                    ),
                    prescription=rng.choice(
                        ["paracetamol 500mg x5d", "rest + fluids", "ibuprofen 400mg", None]
                    ),
                    follow_up_days=rng.choice([None, 7, 14, 30]),
                )
            )
            db.add(
                Invoice(
                    appointment_id=appt.id,
                    amount=prices.get(at, 500.0),
                    currency="INR",
                    status="paid",
                    paid_at=appt_time + timedelta(hours=1),
                )
            )
        elif status == "scheduled" and offset_hours >= 0:
            db.add(
                Invoice(
                    appointment_id=appt.id,
                    amount=prices.get(at, 500.0),
                    currency="INR",
                    status="pending",
                )
            )

    db.commit()
