from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.domain.models import DraftCriteriaIn, JobIn
from app.llm.base import ProviderNotAvailable
from app.llm.registry import get_provider
from app.services import audit
from app.services import jobs as jobs_svc
from app.services import queue as queue_svc
from app.services import screenings as scr_svc
from app.services.ranking import build_ranking
from app.storage.models import Tenant

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post("/draft-criteria")
def draft_criteria(
    data: DraftCriteriaIn,
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        prov = get_provider(tenant.ai_provider, settings, tenant.ai_model or None)
    except ProviderNotAvailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    d = prov.draft_criteria(data.title, data.description)
    return {
        "draft": True,
        "title": data.title,
        "description": d.description,
        "criteria": d.criteria,
        "rules": d.rules,
        "questions": d.questions,
        "weights_total": sum(float(c["weight"]) for c in d.criteria),
        "note": "مسودة للمراجعة. لا يُستخدم شيء منها قبل الاعتماد.",
    }


@router.get("")
def list_jobs(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    out = []
    for j in jobs_svc.list_jobs(db, tenant):
        out.append(jobs_svc.job_out(j, None))
    return {"jobs": out}


@router.put("/{ref}")
def upsert_job(
    ref: str,
    data: JobIn,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    actor: str = Depends(actor_from),
):
    job, version, created = jobs_svc.upsert_job(db, tenant, ref, data, actor)
    db.commit()
    out = jobs_svc.job_out(job, version, job.versions)
    out["new_version"] = created
    return out


@router.get("/{ref}")
def get_job(ref: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    job = jobs_svc.get_job(db, tenant, ref)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return jobs_svc.job_out(job, jobs_svc.active_version(db, job), job.versions)


@router.get("/{ref}/ranking")
def ranking(ref: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    job = jobs_svc.get_job(db, tenant, ref)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return build_ranking(db, tenant, job)


@router.post("/{ref}/rescreen", status_code=202)
def rescreen(
    ref: str,
    request: Request,
    background_tasks: BackgroundTasks,
    force: bool = False,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    job = jobs_svc.get_job(db, tenant, ref)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    version = jobs_svc.active_version(db, job)
    if version is None:
        raise HTTPException(status_code=409, detail="job has no approved version")
    try:
        prov = get_provider(tenant.ai_provider, settings, tenant.ai_model or None)
    except ProviderNotAvailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    queued: list[str] = []
    skipped: list[str] = []
    for s in scr_svc.latest_per_candidate(db, job):
        current, _ = scr_svc.is_current(s, job, s.candidate)
        if current and s.status in ("completed", "needs_review") and not force:
            skipped.append(s.candidate.external_ref)
            continue
        new, created = scr_svc.create_screening(
            db,
            tenant,
            job,
            version,
            s.candidate,
            prov.name,
            prov.model,
            prov.prompt_version,
            settings.profile_schema_version,
            force=force,
            actor=actor,
        )
        if created:
            queued.append(new.id)
        else:
            skipped.append(s.candidate.external_ref)
    audit.log(
        db, tenant.id, ref, "job.rescreen", actor, {"queued": len(queued), "skipped": len(skipped)}
    )
    db.commit()
    for sid in queued:
        queue_svc.dispatch(settings, request.app.state.sessionmaker, sid, background_tasks)
    return {"job_ref": ref, "job_version": version.version, "queued": queued, "skipped": skipped}
