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


def console_user(request: Request) -> str | None:
    from app.console.auth import COOKIE, verify

    return verify(request.app.state.settings, request.cookies.get(COOKIE))


def get_tenant(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> Tenant:
    """API key (adapters) or a console session cookie (the console acts on the default tenant)."""
    if authorization and authorization.lower().startswith("bearer "):
        key = authorization.split(" ", 1)[1].strip()
        tenant = db.scalar(select(Tenant).where(Tenant.api_key_hash == hash_api_key(key)))
        if tenant is None:
            raise HTTPException(status_code=401, detail="invalid API key")
        return tenant
    user = console_user(request)
    if user:
        settings: Settings = request.app.state.settings
        tenant = db.scalar(select(Tenant).where(Tenant.name == settings.tenant_name))
        if tenant is not None:
            return tenant
    raise HTTPException(
        status_code=401, detail="missing API key (Authorization: Bearer <key>) or console session"
    )


def actor_from(request: Request, x_talent_actor: str | None = Header(default=None)) -> str:
    if x_talent_actor:
        return x_talent_actor.strip()[:140]
    user = console_user(request)
    return f"console:{user}" if user else "adapter"
