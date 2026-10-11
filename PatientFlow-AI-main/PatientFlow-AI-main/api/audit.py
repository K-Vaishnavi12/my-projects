"""Tiny helper to record mutations in the audit_log table."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from .models import AuditLog


def audit(
    db: Session,
    entity: str,
    entity_id: str | int,
    action: str,
    diff: Optional[dict[str, Any]] = None,
    actor: Optional[str] = None,
) -> None:
    """Record a mutation. Caller is responsible for the surrounding commit()."""
    db.add(
        AuditLog(
            entity=entity,
            entity_id=str(entity_id),
            action=action,
            diff_json=diff,
            actor=actor,
        )
    )
