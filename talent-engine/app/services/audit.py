"""Audit log: every job and HR action, with ids and hashes only (no personal data)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.storage.models import AuditEvent


def log(
    db: Session,
    tenant_id: str,
    ref: str,
    action: str,
    actor: str = "system",
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    ev = AuditEvent(
        id=new_id("aud"),
        tenant_id=tenant_id,
        ref=ref,
        action=action,
        actor=actor,
        payload=payload or {},
    )
    db.add(ev)
    return ev
