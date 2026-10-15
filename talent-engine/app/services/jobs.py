"""Jobs and their approved versions."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.hashing import hash_obj
from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.domain.models import JobIn
from app.services import audit
from app.storage.models import Job, JobVersion, Tenant


def content_hash(data: JobIn) -> str:
    return hash_obj(
        {
            "title": data.title,
            "description": data.description,
            "criteria": [c.model_dump() for c in data.criteria],
            "rules": [r.model_dump() for r in data.rules],
            "questions": [q.model_dump() for q in data.questions],
        }
    )


def get_job(db: Session, tenant: Tenant, ref: str) -> Job | None:
    return db.scalar(select(Job).where(Job.tenant_id == tenant.id, Job.external_ref == ref))


def list_jobs(db: Session, tenant: Tenant) -> list[Job]:
    return list(db.scalars(select(Job).where(Job.tenant_id == tenant.id).order_by(Job.created_at)))


def get_version(db: Session, job: Job, version: int | None) -> JobVersion | None:
    if version is None:
        return None
    return db.scalar(
        select(JobVersion).where(JobVersion.job_id == job.id, JobVersion.version == version)
    )


def active_version(db: Session, job: Job) -> JobVersion | None:
    return get_version(db, job, job.active_version)


def upsert_job(
    db: Session, tenant: Tenant, ref: str, data: JobIn, actor: str = "adapter"
) -> tuple[Job, JobVersion, bool]:
    """Create the job if needed. A new approved version is created only when the content changed."""
    chash = content_hash(data)
    job = get_job(db, tenant, ref)
    created_job = False
    if job is None:
        job = Job(
            id=new_id("job"),
            tenant_id=tenant.id,
            external_ref=ref,
            title=data.title,
            description=data.description,
        )
        db.add(job)
        db.flush()
        created_job = True
    current = active_version(db, job)
    if current is not None and current.content_hash == chash:
        return job, current, False
    next_no = (max((v.version for v in job.versions), default=0) + 1) if not created_job else 1
    version = JobVersion(
        id=new_id("jv"),
        job_id=job.id,
        version=next_no,
        criteria=[c.model_dump() for c in data.criteria],
        rules=[r.model_dump() for r in data.rules],
        questions=[q.model_dump() for q in data.questions],
        content_hash=chash,
        approved_by=data.approved_by or actor,
        approved_at=utcnow(),
    )
    db.add(version)
    job.title = data.title
    job.description = data.description
    job.active_version = next_no
    audit.log(
        db,
        tenant.id,
        ref,
        "job.version_approved",
        actor,
        {"version": next_no, "content_hash": chash, "approved_by": version.approved_by},
    )
    db.flush()
    return job, version, True


def job_out(
    job: Job, version: JobVersion | None, include_versions: list[JobVersion] | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ref": job.external_ref,
        "title": job.title,
        "description": job.description,
        "active_version": job.active_version,
        "created_at": iso(job.created_at),
        "updated_at": iso(job.updated_at),
    }
    if version is not None:
        out["version"] = {
            "version": version.version,
            "criteria": version.criteria,
            "rules": version.rules,
            "questions": version.questions,
            "weights_total": sum(float(c["weight"]) for c in version.criteria),
            "approved_by": version.approved_by,
            "approved_at": iso(version.approved_at),
            "content_hash": version.content_hash,
        }
    if include_versions is not None:
        out["versions"] = [
            {"version": v.version, "approved_by": v.approved_by, "approved_at": iso(v.approved_at)}
            for v in include_versions
        ]
    return out
