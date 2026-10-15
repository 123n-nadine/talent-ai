"""Candidates: only allowed facts, answers, consent. No names, IDs or photos."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.arabic import normalize
from app.core.hashing import hash_obj
from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.domain.models import CandidateIn
from app.services import audit
from app.storage.models import (
    Candidate,
    CriterionResult,
    Document,
    Embedding,
    Profile,
    Screening,
    Tenant,
)

NUMERIC_FACTS = {"height_cm", "weight_kg", "age"}


def unknown_facts(facts: dict[str, Any], allowed: list[str]) -> list[str]:
    return sorted(k for k in facts if k not in set(allowed))


def normalise_facts(facts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in facts.items():
        if v is None or (isinstance(v, str) and not v.strip()):
            out[k] = None
            continue
        if k in NUMERIC_FACTS:
            try:
                n = float(normalize(str(v)))
                out[k] = int(n) if n.is_integer() else n
            except ValueError:
                out[k] = None
        else:
            out[k] = v.strip() if isinstance(v, str) else v
    return out


def data_hash(
    id_token: str | None, facts: dict[str, Any], answers: dict[str, Any], docs: list[str]
) -> str:
    return hash_obj(
        {"id_token": id_token, "facts": facts, "answers": answers, "documents": sorted(docs)}
    )


def get_candidate(db: Session, tenant: Tenant, ref: str) -> Candidate | None:
    return db.scalar(
        select(Candidate).where(Candidate.tenant_id == tenant.id, Candidate.external_ref == ref)
    )


def list_candidates(db: Session, tenant: Tenant) -> list[Candidate]:
    return list(
        db.scalars(
            select(Candidate).where(Candidate.tenant_id == tenant.id).order_by(Candidate.created_at)
        )
    )


def upsert_candidate(
    db: Session, tenant: Tenant, ref: str, data: CandidateIn, actor: str = "adapter"
) -> tuple[Candidate, bool]:
    facts = normalise_facts(data.facts)
    cand = get_candidate(db, tenant, ref)
    created = cand is None
    if cand is None:
        cand = Candidate(id=new_id("cand"), tenant_id=tenant.id, external_ref=ref, data_hash="")
        db.add(cand)
    cand.id_token = data.id_token
    cand.facts = facts
    cand.answers = data.answers
    cand.consent = data.consent
    days = data.retention_days or tenant.retention_days
    cand.retention_until = utcnow() + timedelta(days=days)
    docs = [d.sha256 for d in cand.documents] if not created else []
    new_hash = data_hash(cand.id_token, cand.facts, cand.answers, docs)
    changed = new_hash != cand.data_hash
    cand.data_hash = new_hash
    audit.log(
        db,
        tenant.id,
        ref,
        "candidate.created" if created else "candidate.updated",
        actor,
        {"data_hash": new_hash, "changed": changed, "consent": data.consent},
    )
    db.flush()
    return cand, created


def delete_candidate(
    db: Session, tenant: Tenant, ref: str, actor: str = "adapter"
) -> dict[str, int]:
    cand = get_candidate(db, tenant, ref)
    if cand is None:
        return {}
    screening_ids = list(db.scalars(select(Screening.id).where(Screening.candidate_id == cand.id)))
    counts = {
        "documents": len(cand.documents),
        "profiles": len(cand.profiles),
        "embeddings": len(cand.embeddings),
        "screenings": len(screening_ids),
    }
    if screening_ids:
        db.execute(delete(CriterionResult).where(CriterionResult.screening_id.in_(screening_ids)))
        db.execute(delete(Screening).where(Screening.id.in_(screening_ids)))
    db.execute(delete(Document).where(Document.candidate_id == cand.id))
    db.execute(delete(Profile).where(Profile.candidate_id == cand.id))
    db.execute(delete(Embedding).where(Embedding.candidate_id == cand.id))
    db.delete(cand)
    audit.log(db, tenant.id, ref, "candidate.deleted", actor, counts)
    db.flush()
    return counts


def candidate_out(
    cand: Candidate, screenings: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ref": cand.external_ref,
        "id_token": cand.id_token,
        "facts": cand.facts,
        "answers": cand.answers,
        "consent": cand.consent,
        "retention_until": iso(cand.retention_until),
        "data_hash": cand.data_hash,
        "documents": [
            {
                "id": d.id,
                "kind": d.kind,
                "mime": d.mime,
                "sha256": d.sha256,
                "status": d.status,
                "extraction_method": d.extraction_method,
                "ocr_confidence": d.ocr_confidence,
            }
            for d in cand.documents
        ],
        "created_at": iso(cand.created_at),
        "updated_at": iso(cand.updated_at),
    }
    if screenings is not None:
        out["screenings"] = screenings
    return out
