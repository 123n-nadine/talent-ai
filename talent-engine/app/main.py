"""Talent Engine API (FastAPI). `create_app()` is used by tests; `app` by uvicorn."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.routers import audit, candidates, console, health, jobs, screenings
from app.api.routers import settings as settings_router
from app.core.config import Settings, get_settings
from app.core.ids import new_id
from app.core.logging import setup_logging
from app.core.security import hash_api_key
from app.services import audit as audit_svc
from app.storage.db import make_engine, make_sessionmaker
from app.storage.models import Base, Tenant


def ensure_default_tenant(sessionmaker, settings: Settings) -> None:
    """Create the default tenant, or rotate its API key when TENANT_API_KEY changed."""
    new_hash = hash_api_key(settings.tenant_api_key)
    with sessionmaker() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.api_key_hash == new_hash))
        if tenant is None:
            by_name = db.scalar(select(Tenant).where(Tenant.name == settings.tenant_name))
            if by_name is not None:
                by_name.api_key_hash = new_hash
                audit_svc.log(
                    db,
                    by_name.id,
                    "tenant",
                    "tenant.key_rotated",
                    "system",
                    {"tenant": by_name.name},
                )
                db.commit()
                return
        if tenant is None:
            tenant = Tenant(
                id=new_id("ten"),
                name=settings.tenant_name,
                api_key_hash=hash_api_key(settings.tenant_api_key),
                callback_url=settings.callback_url or None,
                callback_secret=settings.callback_secret or None,
                ai_provider=settings.ai_provider,
                ai_model=settings.llm_model if settings.ai_provider != "fake" else "fake-rubric-v1",
                ocr_provider=settings.ocr_provider,
                llm_timeout_s=settings.llm_timeout_s,
                max_retries=settings.max_attempts,
                retention_days=settings.retention_days_default,
                allowed_facts=settings.allowed_facts_list,
            )
            db.add(tenant)
        else:
            if not tenant.callback_url and settings.callback_url:
                tenant.callback_url = settings.callback_url
            if not tenant.callback_secret and settings.callback_secret:
                tenant.callback_secret = settings.callback_secret
        db.commit()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    engine = make_engine(settings.database_url)
    sessionmaker = make_sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auto_create_schema or settings.is_sqlite:
            Base.metadata.create_all(engine)
        ensure_default_tenant(sessionmaker, settings)
        yield

    app = FastAPI(
        title="Talent Engine",
        version="0.1.0",
        description="AI screening and ranking engine. The LLM judges, code computes, HR decides.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker

    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(candidates.router)
    app.include_router(screenings.router)
    app.include_router(settings_router.router)
    app.include_router(audit.router)
    app.include_router(console.router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/console")

    return app


app = create_app()
