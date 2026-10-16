from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.domain.models import CandidateIn
from app.services import candidates as cand_svc
from app.services import screenings as scr_svc
from app.storage.models import Screening, Tenant

router = APIRouter(prefix="/v1/candidates", tags=["candidates"])


@router.get("")
def list_candidates(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    return {"candidates": [cand_svc.candidate_out(c) for c in cand_svc.list_candidates(db, tenant)]}


@router.put("/{ref}")
def upsert_candidate(
    ref: str,
    data: CandidateIn,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    """Create or update a candidate. `consent: false` on a candidate that had consent erases
    everything the AI made of the application; only the reference stays (OPEN_QUESTIONS #21)."""
    unknown = cand_svc.unknown_facts(data.facts, tenant.allowed_facts or [])
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "facts not allowed for this tenant",
                "unknown_facts": unknown,
                "allowed_facts": tenant.allowed_facts,
            },
        )
    cand, created = cand_svc.upsert_candidate(db, tenant, ref, data, actor, settings.file_store)
    erased = db.info.get("erasures", {}).get(ref)
    db.commit()
    out = cand_svc.candidate_out(cand)
    out["created"] = created
    if erased is not None:  # what the withdrawal removed; the host refreshes the promoted copies
        out["erased"] = erased
    return out


@router.get("/{ref}")
def get_candidate(ref: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    rows = db.scalars(
        select(Screening)
        .where(Screening.candidate_id == cand.id)
        .order_by(Screening.created_at.desc())
    ).all()
    summaries = [
        {
            "screening_id": s.id,
            "job_ref": s.job.external_ref,
            "job_version": s.job_version.version,
            "status": s.status,
            "score": s.score,
            "band": s.band,
            "eligibility": s.eligibility,
            "current": scr_svc.is_current(s, s.job, cand)[0],
        }
        for s in rows
    ]
    return cand_svc.candidate_out(cand, summaries)


@router.delete("/{ref}")
def delete_candidate(
    ref: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    """Full erasure (the host deleted the application): the AI data and the reference itself."""
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    counts = cand_svc.delete_candidate(db, tenant, ref, actor, settings.file_store)
    db.commit()
    return {"deleted": True, "ref": ref, "removed": counts}
