"""Talent pool (client feature 13): suggestions only, hard rules first, then similarity."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.embeddings.base import EmbeddingUnavailable
from app.embeddings.registry import EMBEDDING_STATUS, get_embedding_provider
from app.services import jobs as jobs_svc
from app.services import talent_pool as pool
from app.storage.models import Candidate, Embedding, Tenant

router = APIRouter(prefix="/v1/talent-pool", tags=["talent-pool"])


class SearchIn(BaseModel):
    job_ref: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=200)


@router.post("/search")
def search(
    data: SearchIn,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    job = jobs_svc.get_job(db, tenant, data.job_ref)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    version = jobs_svc.active_version(db, job)
    if version is None:
        raise HTTPException(status_code=409, detail="job has no approved version")
    try:
        out = pool.search(
            db, tenant, job, version, get_embedding_provider(settings), data.limit, actor
        )
    except EmbeddingUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    db.commit()
    return out


@router.get("/status")
def status(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    indexed = db.scalar(
        select(func.count(Embedding.id)).join(Candidate).where(Candidate.tenant_id == tenant.id)
    )
    return {
        "provider": settings.embedding_provider,
        "model": settings.embedding_model,
        "note": EMBEDDING_STATUS.get(settings.embedding_provider, ""),
        "indexed_profiles": indexed or 0,
    }


@router.post("/reindex")
def reindex(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        out = pool.reindex(db, tenant, get_embedding_provider(settings), settings.pool_cv_chars)
    except EmbeddingUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    db.commit()
    return out
