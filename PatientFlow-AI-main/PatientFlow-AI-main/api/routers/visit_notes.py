"""Visit notes (1:1 with appointments)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..audit import audit
from ..db import get_db
from ..models import Appointment, VisitNote
from ..schemas import VisitNoteCreate, VisitNoteOut

router = APIRouter(prefix="/visit-notes", tags=["visit_notes"])


@router.get("", response_model=list[VisitNoteOut])
def list_notes(appointment_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(VisitNote)
    if appointment_id is not None:
        q = q.filter(VisitNote.appointment_id == appointment_id)
    return q.order_by(VisitNote.created_at.desc()).all()


@router.post("", response_model=VisitNoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: VisitNoteCreate, db: Session = Depends(get_db)):
    if not db.get(Appointment, payload.appointment_id):
        raise HTTPException(400, f"Unknown appointment_id {payload.appointment_id}")
    if db.query(VisitNote).filter(VisitNote.appointment_id == payload.appointment_id).first():
        raise HTTPException(400, "visit note already exists for this appointment")
    n = VisitNote(**payload.model_dump())
    db.add(n)
    db.flush()
    audit(db, "visit_note", n.id, "create", diff=payload.model_dump())
    db.commit()
    db.refresh(n)
    return n


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    n = db.get(VisitNote, note_id)
    if not n:
        raise HTTPException(404, "note not found")
    audit(db, "visit_note", n.id, "delete")
    db.delete(n)
    db.commit()
