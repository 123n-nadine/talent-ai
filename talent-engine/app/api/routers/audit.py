from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant
from app.core.timeutil import iso
from app.storage.models import AuditEvent, Tenant

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("")
def list_audit(
    ref: str | None = None,
    action: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
):
    q = select(AuditEvent).where(AuditEvent.tenant_id == tenant.id)
    if ref:
        q = q.where(AuditEvent.ref == ref)
    if action:
        q = q.where(AuditEvent.action == action)
    rows = db.scalars(q.order_by(AuditEvent.at.desc()).limit(min(limit, 1000))).all()
    return {
        "events": [
            {
                "id": e.id,
                "ref": e.ref,
                "action": e.action,
                "actor": e.actor,
                "at": iso(e.at),
                "payload": e.payload,
            }
            for e in rows
        ]
    }
