from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.domain.models import OverrideIn, ScreeningCreate
from app.llm.base import ProviderNotAvailable
from app.llm.registry import get_provider
from app.services import candidates as cand_svc
from app.services import jobs as jobs_svc
from app.services import queue as queue_svc
from app.services import screenings as scr_svc
from app.services.ranking import rank_of
from app.storage.models import Candidate, Job, Screening, Tenant

router = APIRouter(prefix="/v1/screenings", tags=["screenings"])


def _out(db: Session, tenant: Tenant, s: Screening) -> dict:
    rank, total = rank_of(db, tenant, s)
    return scr_svc.to_out(s, rank, total, with_cv=True)


@router.post("", status_code=202)
def create_screening(
    data: ScreeningCreate,
    request: Request,
    background_tasks: BackgroundTasks,
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
    cand = cand_svc.get_candidate(db, tenant, data.candidate_ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    try:
        prov = get_provider(tenant.ai_provider, settings, tenant.ai_model or None)
    except ProviderNotAvailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    s, created = scr_svc.create_screening(
        db,
        tenant,
        job,
        version,
        cand,
        prov.name,
        prov.model,
        prov.prompt_version,
        settings.profile_schema_version,
        force=data.force,
        actor=actor,
    )
    db.commit()
    if created:
        queue_svc.dispatch(settings, request.app.state.sessionmaker, s.id, background_tasks)
    return {
        "screening_id": s.id,
        "status": s.status,
        "created": created,
        "duplicate_of": s.duplicate_of,
        "input_hash": s.input_hash,
    }


@router.get("")
def list_screenings(
    job_ref: str | None = None,
    candidate_ref: str | None = None,
    status: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
):
    q = select(Screening).where(Screening.tenant_id == tenant.id)
    if job_ref:
        q = q.join(Job, Job.id == Screening.job_id).where(Job.external_ref == job_ref)
    if candidate_ref:
        q = q.join(Candidate, Candidate.id == Screening.candidate_id).where(
            Candidate.external_ref == candidate_ref
        )
    if status:
        q = q.where(Screening.status == status)
    rows = db.scalars(q.order_by(Screening.created_at.desc()).limit(min(limit, 1000))).all()
    return {"screenings": [scr_svc.to_out(s) for s in rows]}


@router.get("/{screening_id}")
def get_screening(
    screening_id: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)
):
    s = scr_svc.get_screening(db, tenant, screening_id)
    if s is None:
        raise HTTPException(status_code=404, detail="screening not found")
    return _out(db, tenant, s)


@router.post("/{screening_id}/override")
def override(
    screening_id: str,
    data: OverrideIn,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
):
    s = scr_svc.get_screening(db, tenant, screening_id)
    if s is None:
        raise HTTPException(status_code=404, detail="screening not found")
    try:
        scr_svc.apply_override(db, tenant, s, data)
    except scr_svc.ScreeningError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    db.commit()
    db.refresh(s)
    return _out(db, tenant, s)


@router.post("/{screening_id}/retry", status_code=202)
def retry(
    screening_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    s = scr_svc.get_screening(db, tenant, screening_id)
    if s is None:
        raise HTTPException(status_code=404, detail="screening not found")
    try:
        scr_svc.mark_for_retry(db, tenant, s, actor)
    except scr_svc.ScreeningError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    db.commit()
    queue_svc.dispatch(settings, request.app.state.sessionmaker, s.id, background_tasks)
    return {"screening_id": s.id, "status": "queued"}
