"""FastAPI dependencies: DB session, settings, tenant from the API key."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_api_key
from app.storage.models import Tenant


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    db: Session = request.app.state.sessionmaker()
    try:
        yield db
    finally:
        db.close()


def get_tenant(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> Tenant:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing API key (Authorization: Bearer <key>)")
    key = authorization.split(" ", 1)[1].strip()
    tenant = db.scalar(select(Tenant).where(Tenant.api_key_hash == hash_api_key(key)))
    if tenant is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    return tenant


def actor_from(x_talent_actor: str | None = Header(default=None)) -> str:
    return (x_talent_actor or "adapter").strip()[:140]
