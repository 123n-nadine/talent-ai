"""Screenings: creation (dedupe, duplicates), serialisation, overrides, retries, stale detection."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.hashing import hash_obj
from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.domain.labels import AI_STATUS, SCORE_DISCLAIMER, STAGES
from app.domain.models import OverrideIn
from app.scoring.score import JudgedCriterion, compute, summary_text
from app.services import audit
from app.storage.models import Candidate, CriterionResult, Job, JobVersion, Screening, Tenant

SCORE_FLAGS = {
    "missing_evidence",
    "mandatory_missing",
    "mandatory_zero",
    "low_coverage",
    "contradiction",
    "hr_override",
}


class ScreeningError(ValueError):
    pass


def input_hash(
    version: JobVersion, candidate: Candidate, provider: str, model: str, prompt: str, schema: str
) -> str:
    return hash_obj(
        {
            "job_version": version.content_hash,
            "candidate_ref": candidate.external_ref,
            "candidate": candidate.data_hash,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "profile_schema": schema,
        }
    )


def find_duplicate_of(db: Session, tenant: Tenant, job: Job, candidate: Candidate) -> str | None:
    """Earliest other candidate of this tenant with the same id_token that applied to the same job."""
    if not candidate.id_token:
        return None
    peers = db.scalars(
        select(Candidate)
        .where(
            Candidate.tenant_id == tenant.id,
            Candidate.id_token == candidate.id_token,
            Candidate.id != candidate.id,
        )
        .order_by(Candidate.created_at, Candidate.external_ref)
    ).all()
    me = (candidate.created_at, candidate.external_ref)
    for p in peers:
        if (p.created_at, p.external_ref) >= me:
            continue  # only an EARLIER application can be the original
        has = db.scalar(
            select(Screening.id)
            .where(Screening.job_id == job.id, Screening.candidate_id == p.id)
            .limit(1)
        )
        if has:
            return p.external_ref
    return None


def initial_stages() -> list[dict[str, Any]]:
    return [
        {"key": k, "label_ar": ar, "label_en": en, "status": "pending", "note": None}
        for k, ar, en in STAGES
    ]


def create_screening(
    db: Session,
    tenant: Tenant,
    job: Job,
    version: JobVersion,
    candidate: Candidate,
    provider_name: str,
    model: str,
    prompt_version: str,
    schema_version: str,
    force: bool = False,
    actor: str = "adapter",
) -> tuple[Screening, bool]:
    ihash = input_hash(version, candidate, provider_name, model, prompt_version, schema_version)
    if not force:
        existing = db.scalar(
            select(Screening)
            .where(
                Screening.tenant_id == tenant.id,
                Screening.input_hash == ihash,
                Screening.status != "failed",
            )
            .order_by(Screening.created_at.desc())
        )
        if existing is not None:
            return existing, False
    dup_of = find_duplicate_of(db, tenant, job, candidate)
    s = Screening(
        id=new_id("scr"),
        tenant_id=tenant.id,
        job_id=job.id,
        job_version_id=version.id,
        candidate_id=candidate.id,
        status="queued",
        stages=initial_stages(),
        flags=["duplicate"] if dup_of else [],
        duplicate_of=dup_of,
        input_hash=ihash,
        candidate_data_hash=candidate.data_hash,
        versions={
            "provider": provider_name,
            "model": model,
            "prompt": prompt_version,
            "profile_schema": schema_version,
        },
    )
    db.add(s)
    audit.log(
        db,
        tenant.id,
        candidate.external_ref,
        "screening.created",
        actor,
        {
            "screening_id": s.id,
            "job_ref": job.external_ref,
            "job_version": version.version,
            "input_hash": ihash,
            "duplicate_of": dup_of,
        },
    )
    db.flush()
    return s, True


def get_screening(db: Session, tenant: Tenant, screening_id: str) -> Screening | None:
    return db.scalar(
        select(Screening).where(Screening.tenant_id == tenant.id, Screening.id == screening_id)
    )


def latest_per_candidate(db: Session, job: Job) -> list[Screening]:
    rows = db.scalars(
        select(Screening).where(Screening.job_id == job.id).order_by(Screening.created_at.desc())
    ).all()
    seen: set[str] = set()
    out: list[Screening] = []
    for s in rows:
        if s.candidate_id in seen:
            continue
        seen.add(s.candidate_id)
        out.append(s)
    return out


def is_current(s: Screening, job: Job, candidate: Candidate) -> tuple[bool, str | None]:
    if s.job_version.version != job.active_version:
        return False, "stale"
    if s.candidate_data_hash != candidate.data_hash:
        return False, "data_changed"
    return True, None


def rows_from_results(results: list[CriterionResult]) -> list[JudgedCriterion]:
    return [
        JudgedCriterion(
            key=r.criterion_key,
            text=r.text,
            weight=r.weight,
            mandatory=r.mandatory,
            level=r.level,
            source=r.source if r.source != "hr_override" else "form_field",
            field=r.field,
            evidence=r.evidence_text,
            missing_evidence=r.missing_evidence,
            contradiction=r.contradiction,
            confirmed_by_cv=r.confirmed_by_cv,
            overridden_level=r.overridden_level,
            override_reason=r.override_reason,
            override_by=r.override_by,
        )
        for r in results
    ]


def recompute(s: Screening) -> None:
    """Recompute score fields from the stored criterion results (after an override)."""
    result = compute(rows_from_results(s.criteria))
    extra = [f for f in (s.flags or []) if f not in SCORE_FLAGS]
    s.score = result.score
    s.coverage = result.coverage
    s.band = result.band
    s.needs_review = result.needs_review
    s.flags = sorted(set(result.flags) | set(extra))
    s.strengths = result.strengths
    s.gaps = result.gaps
    s.raise_score = result.raise_score
    s.summary = summary_text(result, s.eligibility or "eligible", s.eligibility_reasons or [])
    s.status = (
        "needs_review" if (result.needs_review or s.eligibility == "needs_review") else "completed"
    )


def apply_override(db: Session, tenant: Tenant, s: Screening, data: OverrideIn) -> Screening:
    if s.status not in ("completed", "needs_review"):
        raise ScreeningError("only completed screenings can be overridden")
    row = next((r for r in s.criteria if r.criterion_key == data.criterion_key), None)
    if row is None:
        raise ScreeningError(f"unknown criterion '{data.criterion_key}'")
    before = row.overridden_level if row.overridden_level is not None else row.level
    row.overridden_level = int(data.level)
    row.override_reason = data.reason
    row.override_by = data.by
    row.override_at = utcnow()
    recompute(s)
    audit.log(
        db,
        tenant.id,
        s.candidate.external_ref,
        "screening.override",
        data.by,
        {
            "screening_id": s.id,
            "criterion": data.criterion_key,
            "from": before,
            "to": int(data.level),
            "reason": data.reason,
            "score": s.score,
        },
    )
    db.flush()
    return s


def mark_for_retry(db: Session, tenant: Tenant, s: Screening, actor: str) -> Screening:
    if s.status not in ("failed",):
        raise ScreeningError("only failed screenings can be retried")
    s.status = "queued"
    s.error = None
    s.attempts = 0
    s.stages = initial_stages()
    audit.log(
        db, tenant.id, s.candidate.external_ref, "screening.retry", actor, {"screening_id": s.id}
    )
    db.flush()
    return s


def to_out(
    s: Screening, rank: int | None = None, ranked_total: int | None = None
) -> dict[str, Any]:
    job, version, cand = s.job, s.job_version, s.candidate
    current, why = is_current(s, job, cand)
    flags = list(s.flags or [])
    if why and why not in flags:
        flags.append(why)
    criteria = []
    for r in s.criteria:
        effective = (
            r.overridden_level
            if r.overridden_level is not None
            else (0 if r.missing_evidence else r.level)
        )
        criteria.append(
            {
                "key": r.criterion_key,
                "text": r.text,
                "weight": r.weight,
                "mandatory": r.mandatory,
                "level": r.level,
                "effective_level": effective,
                "source": r.source,
                "field": r.field,
                "evidence": r.evidence_text,
                "missing_evidence": r.missing_evidence,
                "contradiction": r.contradiction,
                "confirmed_by_cv": r.confirmed_by_cv,
                "overridden_level": r.overridden_level,
                "override_reason": r.override_reason,
                "override_by": r.override_by,
                "override_at": iso(r.override_at),
            }
        )
    return {
        "screening_id": s.id,
        "job_ref": job.external_ref,
        "job_title": job.title,
        "job_version": version.version,
        "candidate_ref": cand.external_ref,
        "status": s.status,
        "ai_status": AI_STATUS.get(s.status, "Processing"),
        "current": current,
        "stale_reason": why,
        "duplicate_of": s.duplicate_of,
        "eligibility": s.eligibility,
        "eligibility_reasons": s.eligibility_reasons or [],
        "eligibility_checks": s.eligibility_checks or [],
        "score": s.score,
        "coverage": s.coverage,
        "band": s.band,
        "needs_review": s.needs_review,
        "flags": sorted(set(flags)),
        "criteria": criteria,
        "summary": s.summary,
        "strengths": s.strengths or [],
        "gaps": s.gaps or [],
        "raise_score": s.raise_score or [],
        "rank": rank,
        "ranked_total": ranked_total,
        "versions": s.versions or {},
        "input_hash": s.input_hash,
        "stages": s.stages or [],
        "attempts": s.attempts,
        "error": s.error,
        "created_at": iso(s.created_at),
        "started_at": iso(s.started_at),
        "completed_at": iso(s.completed_at),
        "disclaimer": SCORE_DISCLAIMER,
    }
