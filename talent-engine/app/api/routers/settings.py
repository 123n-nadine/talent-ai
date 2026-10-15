from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.domain.models import SettingsIn
from app.services import settings as settings_svc
from app.storage.models import Tenant

router = APIRouter(prefix="/v1/settings", tags=["settings"])


@router.get("")
def get_settings(
    tenant: Tenant = Depends(get_tenant), settings: Settings = Depends(get_settings_dep)
):
    return settings_svc.settings_out(tenant, settings)


@router.put("")
def put_settings(
    data: SettingsIn,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    try:
        settings_svc.update_settings(db, tenant, data, settings, actor)
    except settings_svc.SettingsError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    db.commit()
    return settings_svc.settings_out(tenant, settings)
