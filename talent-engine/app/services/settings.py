"""Tenant settings: the engine owns the AI/OCR provider values (decision 13)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import SettingsIn
from app.llm.registry import PROVIDER_STATUS, provider_available
from app.services import audit
from app.storage.models import Tenant


class SettingsError(ValueError):
    pass


def settings_out(tenant: Tenant, settings: Settings) -> dict[str, Any]:
    ok, why = provider_available(tenant.ai_provider, settings)
    return {
        "tenant": tenant.name,
        "ai_provider": tenant.ai_provider,
        "ai_model": tenant.ai_model,
        "ocr_provider": tenant.ocr_provider,
        "llm_timeout_s": tenant.llm_timeout_s,
        "max_retries": tenant.max_retries,
        "retention_days": tenant.retention_days,
        "allowed_facts": tenant.allowed_facts,
        "callback_url": tenant.callback_url,
        "callback_secret_set": bool(tenant.callback_secret),
        "provider_ready": ok,
        "provider_note": why,
        "providers": PROVIDER_STATUS,
        "defaults_from_env": {
            "ai_provider": settings.ai_provider,
            "llm_model": settings.llm_model,
            "ocr_provider": settings.ocr_provider,
        },
    }


def update_settings(
    db: Session, tenant: Tenant, data: SettingsIn, settings: Settings, actor: str = "adapter"
) -> Tenant:
    changes: dict[str, Any] = {}
    if data.ai_provider is not None and data.ai_provider != tenant.ai_provider:
        ok, why = provider_available(data.ai_provider, settings)
        if not ok:
            raise SettingsError(why)
        changes["ai_provider"] = data.ai_provider
    for fld in (
        "ai_model",
        "ocr_provider",
        "llm_timeout_s",
        "max_retries",
        "retention_days",
        "callback_url",
    ):
        val = getattr(data, fld)
        if val is not None and val != getattr(tenant, fld):
            changes[fld] = val
    if data.allowed_facts is not None and data.allowed_facts != tenant.allowed_facts:
        changes["allowed_facts"] = sorted(set(data.allowed_facts))
    if data.callback_secret is not None and data.callback_secret != tenant.callback_secret:
        tenant.callback_secret = data.callback_secret
        changes["callback_secret"] = "(updated)"
    for k, v in changes.items():
        if k != "callback_secret":
            setattr(tenant, k, v)
    if changes:
        audit.log(db, tenant.id, "settings", "settings.updated", actor, changes)
        db.flush()
    return tenant
