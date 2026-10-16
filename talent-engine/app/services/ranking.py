"""Ranking per job: only completed + eligible + current + non-duplicate screenings are ranked;
everything else is grouped with a reason (ARCHITECTURE §5)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timeutil import iso
from app.domain.labels import GROUP_REASONS, SCORE_DISCLAIMER
from app.services.screenings import is_current, latest_per_candidate
from app.storage.models import Candidate, Job, Screening, Tenant

GROUP_ORDER = [
    "not_eligible",
    "needs_review",
    "processing",
    "failed",
    "stale",
    "duplicate",
    "consent_withdrawn",
]


def classify(s: Screening, job: Job) -> tuple[str, str, str]:
    """Return (group, reason_ar, reason_en); group 'ranked' means it is ranked."""
    if s.duplicate_of:
        ar, en = GROUP_REASONS["duplicate"]
        return "duplicate", f"{ar} ({s.duplicate_of})", f"{en} ({s.duplicate_of})"
    if s.status in ("queued", "processing"):
        return ("processing", *GROUP_REASONS["processing"])
    if s.status == "failed":
        ar, en = GROUP_REASONS["failed"]
        err = f" — {s.error}" if s.error else ""
        return "failed", ar + err, en + err
    current, why = is_current(s, job, s.candidate)
    if not current:
        ar, en = GROUP_REASONS["data_changed" if why == "data_changed" else "stale"]
        return "stale", ar, en
    if s.eligibility == "not_eligible":
        ar, en = GROUP_REASONS["not_eligible"]
        reasons = [r for r in (s.eligibility_reasons or [])]
        return "not_eligible", ar + (": " + "؛ ".join(reasons) if reasons else ""), en
    if s.status == "needs_review" or s.eligibility == "needs_review":
        return ("needs_review", *GROUP_REASONS["needs_review"])
    return "ranked", "", ""


def _item(s: Screening, rank: int | None, reason_ar: str, reason_en: str) -> dict[str, Any]:
    return {
        "rank": rank,
        "candidate_ref": s.candidate.external_ref,
        "screening_id": s.id,
        "status": s.status,
        "score": s.score,
        "coverage": s.coverage,
        "band": s.band,
        "eligibility": s.eligibility,
        "flags": s.flags or [],
        "strengths": [x["key"] for x in (s.strengths or [])],
        "job_version": s.job_version.version,
        "reason_ar": reason_ar or None,
        "reason_en": reason_en or None,
        "created_at": iso(s.created_at),
        "completed_at": iso(s.completed_at),
        "duplicate_of": s.duplicate_of,
        "needs_review": s.needs_review,
    }


def _withdrawn_item(c: Candidate) -> dict[str, Any]:
    """Only the reference and the date: no score, no details (the AI data is gone)."""
    ar, en = GROUP_REASONS["consent_withdrawn"]
    return {
        "rank": None,
        "candidate_ref": c.external_ref,
        "screening_id": None,
        "status": "consent_withdrawn",
        "score": None,
        "coverage": None,
        "band": None,
        "eligibility": None,
        "flags": [],
        "strengths": [],
        "job_version": None,
        "reason_ar": ar,
        "reason_en": en,
        "created_at": None,
        "completed_at": None,
        "withdrawn_at": iso(c.consent_withdrawn_at),
        "duplicate_of": None,
        "needs_review": False,
    }


def withdrawn_from_job(db: Session, tenant: Tenant, job: Job) -> list[Candidate]:
    rows = db.scalars(
        select(Candidate).where(
            Candidate.tenant_id == tenant.id,
            Candidate.consent.is_(False),
            Candidate.consent_withdrawn_at.is_not(None),
        )
    ).all()
    return sorted(
        (c for c in rows if job.external_ref in (c.withdrawn_from or [])),
        key=lambda c: c.external_ref,
    )


def build_ranking(db: Session, tenant: Tenant, job: Job) -> dict[str, Any]:
    screenings = latest_per_candidate(db, job)
    ranked: list[Screening] = []
    groups: dict[str, list[dict[str, Any]]] = {g: [] for g in GROUP_ORDER}
    for s in screenings:
        group, ar, en = classify(s, job)
        if group == "ranked":
            ranked.append(s)
        else:
            groups[group].append(_item(s, None, ar, en))
    ranked.sort(
        key=lambda s: (
            -(s.score or 0),
            -(s.coverage or 0),
            s.candidate.created_at,
            s.candidate.external_ref,
        )
    )
    for g in groups.values():
        g.sort(key=lambda x: (-(x["score"] or 0), x["candidate_ref"]))
    withdrawn = withdrawn_from_job(db, tenant, job)
    groups["consent_withdrawn"] = [_withdrawn_item(c) for c in withdrawn]
    return {
        "job_ref": job.external_ref,
        "job_title": job.title,
        "job_version": job.active_version,
        "total": len(screenings) + len(withdrawn),
        "ranked_total": len(ranked),
        "ranked": [_item(s, i + 1, "", "") for i, s in enumerate(ranked)],
        "groups": groups,
        "disclaimer": SCORE_DISCLAIMER,
    }


def rank_of(db: Session, tenant: Tenant, s: Screening) -> tuple[int | None, int]:
    r = build_ranking(db, tenant, s.job)
    for item in r["ranked"]:
        if item["screening_id"] == s.id:
            return item["rank"], r["ranked_total"]
    return None, r["ranked_total"]
