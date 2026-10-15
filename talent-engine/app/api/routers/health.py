from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from app.api.deps import get_settings_dep
from app.core.config import Settings
from app.llm.registry import provider_available
from app.storage.models import Tenant

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "talent-engine", "version": "0.1.0"}


@router.get("/ready")
def ready(request: Request, settings: Settings = Depends(get_settings_dep)):
    checks: dict[str, dict] = {}
    ok = True
    try:
        with request.app.state.sessionmaker() as db:
            db.execute(text("SELECT 1"))
            tenants = db.scalars(select(Tenant)).all()
        checks["db"] = {"ok": True}
    except Exception as e:  # noqa: BLE001
        checks["db"] = {"ok": False, "error": str(e)[:200]}
        tenants = []
        ok = False
    if settings.queue_mode == "rq":
        try:
            from redis import Redis

            Redis.from_url(settings.redis_url).ping()
            checks["redis"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            checks["redis"] = {"ok": False, "error": str(e)[:200]}
            ok = False
    else:
        checks["redis"] = {"ok": True, "note": "inline queue"}
    for t in tenants:
        p_ok, note = provider_available(t.ai_provider, settings, t.ai_model or None, probe=True)
        checks[f"llm:{t.name}"] = {"ok": p_ok, "provider": t.ai_provider, "note": note}
        ok = ok and p_ok
    checks["ocr"] = {"ok": True, "provider": settings.ocr_provider, "note": "phase 2"}
    return JSONResponse({"ready": ok, "checks": checks}, status_code=200 if ok else 503)
