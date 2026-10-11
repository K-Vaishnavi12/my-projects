"""Invoices (1:1 with appointments)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..audit import audit
from ..db import get_db
from ..models import Appointment, Invoice
from ..schemas import InvoiceCreate, InvoiceOut, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status_: str | None = None,
    appointment_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)
    if status_:
        q = q.filter(Invoice.status == status_)
    if appointment_id is not None:
        q = q.filter(Invoice.appointment_id == appointment_id)
    return q.order_by(Invoice.issued_at.desc()).all()


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    if not db.get(Appointment, payload.appointment_id):
        raise HTTPException(400, f"Unknown appointment_id {payload.appointment_id}")
    if db.query(Invoice).filter(Invoice.appointment_id == payload.appointment_id).first():
        raise HTTPException(400, "invoice already exists for this appointment")
    inv = Invoice(**payload.model_dump())
    db.add(inv)
    db.flush()
    audit(db, "invoice", inv.id, "create", diff=payload.model_dump())
    db.commit()
    db.refresh(inv)
    return inv


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "invoice not found")
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(inv, k, v)
    if changes.get("status") == "paid" and inv.paid_at is None:
        inv.paid_at = datetime.utcnow()
    audit(db, "invoice", inv.id, "update", diff=changes)
    db.commit()
    db.refresh(inv)
    return inv
