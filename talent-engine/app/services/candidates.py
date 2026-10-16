"""Candidates: only allowed facts, answers, consent. No names, IDs or photos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.arabic import normalize
from app.core.hashing import hash_obj
from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.documents.store import release_files
from app.domain.models import CandidateIn
from app.services import audit
from app.storage.models import (
    AuditEvent,
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


def doc_fingerprint(doc: Document) -> str:
    """sha256 of the file plus the extraction outcome: re-processing a CV changes the input."""
    return f"{doc.sha256}:{doc.status}:{hash_obj(doc.redacted_text or '')}"


def data_hash(
    id_token: str | None, facts: dict[str, Any], answers: dict[str, Any], docs: list[str]
) -> str:
    return hash_obj(
        {"id_token": id_token, "facts": facts, "answers": answers, "documents": sorted(docs)}
    )


def get_candidate(db: Session, tenant: Tenant, ref: str, lock: bool = False) -> Candidate | None:
    q = select(Candidate).where(Candidate.tenant_id == tenant.id, Candidate.external_ref == ref)
    # lock: a screening finishing at the same moment waits for the withdrawal, or the other way round
    return db.scalar(q.with_for_update() if lock else q)


def list_candidates(db: Session, tenant: Tenant) -> list[Candidate]:
    return list(
        db.scalars(
            select(Candidate).where(Candidate.tenant_id == tenant.id).order_by(Candidate.created_at)
        )
    )


def upsert_candidate(
    db: Session,
    tenant: Tenant,
    ref: str,
    data: CandidateIn,
    actor: str = "adapter",
    file_store: str | None = None,
) -> tuple[Candidate, bool]:
    cand = get_candidate(db, tenant, ref, lock=not data.consent)
    created = cand is None
    if cand is None:
        cand = Candidate(id=new_id("cand"), tenant_id=tenant.id, external_ref=ref, data_hash="")
        db.add(cand)
    if not data.consent:
        return _without_consent(db, tenant, cand, created, data, actor, file_store), created
    if not created and not cand.consent:  # consent given again: the candidate starts afresh
        cand.consent_withdrawn_at = None
        cand.withdrawn_from = []
    facts = normalise_facts(data.facts)
    cand.id_token = data.id_token
    cand.facts = facts
    cand.answers = data.answers
    cand.consent = True
    _applied(cand, data, tenant)
    docs = [doc_fingerprint(d) for d in cand.documents] if not created else []
    new_hash = data_hash(cand.id_token, cand.facts, cand.answers, docs)
    changed = new_hash != cand.data_hash
    cand.data_hash = new_hash
    audit.log(
        db,
        tenant.id,
        ref,
        "candidate.created" if created else "candidate.updated",
        actor,
        {"data_hash": new_hash, "changed": changed, "consent": True},
    )
    db.flush()
    return cand, created


def _applied(cand: Candidate, data: CandidateIn, tenant: Tenant) -> None:
    if data.applied_at is not None:
        at = data.applied_at
        cand.applied_at = at.astimezone(UTC) if at.tzinfo else at.replace(tzinfo=UTC)
    elif cand.applied_at is None:
        cand.applied_at = utcnow()
    days = data.retention_days or tenant.retention_days
    cand.retention_until = cand.applied_at + timedelta(days=days)


def _without_consent(
    db: Session,
    tenant: Tenant,
    cand: Candidate,
    created: bool,
    data: CandidateIn,
    actor: str,
    file_store: str | None,
) -> Candidate:
    """No consent to AI processing: the engine keeps nothing about the person. A consent that is
    withdrawn erases what the AI made of the application (OPEN_QUESTIONS #21, default decided by
    Nadine on 2026-10-16 until the client confirms); a candidate sent without consent is stored
    as a bare reference that no screening may use."""
    if not created and cand.consent:
        erase_ai_data(db, tenant, cand, actor, file_store, reason="consent_withdrawn")
        return cand
    cand.consent = False
    cand.id_token, cand.facts, cand.answers = None, {}, {}
    if created:
        _applied(cand, data, tenant)
        cand.withdrawn_from = []
    cand.data_hash = data_hash(None, {}, {}, [])
    audit.log(
        db,
        tenant.id,
        cand.external_ref,
        "candidate.created" if created else "candidate.updated",
        actor,
        {"consent": False},
    )
    db.flush()
    return cand


def _applied_order(s: Screening) -> tuple[datetime, str]:
    at = s.candidate.applied_at or s.candidate.created_at
    return (at if at.tzinfo else at.replace(tzinfo=UTC), s.candidate.external_ref)


def _promote_copies(db: Session, tenant: Tenant, cand: Candidate) -> list[str]:
    """Later applications of the same person were grouped as duplicates of this one: the earliest
    of them becomes the original (per job), the others now point to it."""
    copies = db.scalars(
        select(Screening).where(
            Screening.tenant_id == tenant.id, Screening.duplicate_of == cand.external_ref
        )
    ).all()
    by_job: dict[str, list[Screening]] = {}
    for c in copies:
        by_job.setdefault(c.job_id, []).append(c)
    promoted: list[str] = []
    for rows in by_job.values():
        rows.sort(key=_applied_order)
        first = rows[0]
        first.duplicate_of = None
        first.flags = sorted(set(first.flags or []) - {"duplicate"})
        promoted.append(first.candidate.external_ref)
        for r in rows[1:]:
            r.duplicate_of = first.candidate.external_ref
        for r in rows:
            audit.log(
                db,
                tenant.id,
                r.candidate.external_ref,
                "screening.duplicate_of_changed",
                "system",
                {
                    "screening_id": r.id,
                    "duplicate_of": r.duplicate_of,
                    "because": "original erased",
                },
            )
    return promoted


def _scrub_audit(db: Session, tenant: Tenant, ref: str) -> int:
    """The audit trail keeps what happened (action, actor, time) but no longer what the AI found."""
    n = 0
    for e in db.scalars(
        select(AuditEvent).where(AuditEvent.tenant_id == tenant.id, AuditEvent.ref == ref)
    ):
        if e.payload and e.payload != {"erased": True}:
            e.payload = {"erased": True}
            n += 1
    return n


def erase_ai_data(
    db: Session,
    tenant: Tenant,
    cand: Candidate,
    actor: str = "adapter",
    file_store: str | None = None,
    reason: str = "consent_withdrawn",
) -> dict[str, Any]:
    """Forget everything the AI made of this candidate: CV documents (and their files when no other
    document holds them), the structured profiles, the talent-pool index, every screening with
    its criterion results, the facts and answers copied from the host, and the findings written
    in the audit trail. Only the reference stays, with the jobs it had applied to."""
    screenings = list(db.scalars(select(Screening).where(Screening.candidate_id == cand.id)))
    jobs = sorted({s.job.external_ref for s in screenings} | set(cand.withdrawn_from or []))
    counts: dict[str, Any] = {
        "documents": len(cand.documents),
        "profiles": len(cand.profiles),
        "embeddings": len(cand.embeddings),
        "screenings": len(screenings),
    }
    counts["promoted"] = _promote_copies(db, tenant, cand)
    ids = [s.id for s in screenings]
    if ids:
        db.execute(delete(CriterionResult).where(CriterionResult.screening_id.in_(ids)))
        db.execute(delete(Screening).where(Screening.id.in_(ids)))
    released: set[str | None] = set()
    for d in list(cand.documents):
        released |= {d.sha256, d.preview_sha256}
        db.delete(d)
    db.execute(delete(Profile).where(Profile.candidate_id == cand.id))
    db.execute(delete(Embedding).where(Embedding.candidate_id == cand.id))
    db.flush()
    counts["files"] = release_files(db, file_store, released) if file_store else 0
    db.expire(cand, ["documents", "profiles", "embeddings", "screenings"])
    cand.consent = False
    cand.id_token, cand.facts, cand.answers = None, {}, {}
    cand.data_hash = data_hash(None, {}, {}, [])
    if reason == "consent_withdrawn":
        cand.consent_withdrawn_at = cand.consent_withdrawn_at or utcnow()
        cand.withdrawn_from = jobs
    counts["audit_scrubbed"] = _scrub_audit(db, tenant, cand.external_ref)
    if reason == "consent_withdrawn":  # a deletion logs its own event
        audit.log(db, tenant.id, cand.external_ref, "candidate.consent_withdrawn", actor, counts)
    db.info.setdefault("erasures", {})[cand.external_ref] = counts
    db.flush()
    return counts


def delete_candidate(
    db: Session, tenant: Tenant, ref: str, actor: str = "adapter", file_store: str | None = None
) -> dict[str, Any]:
    cand = get_candidate(db, tenant, ref, lock=True)
    if cand is None:
        return {}
    counts = erase_ai_data(db, tenant, cand, actor, file_store, reason="erased")
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
        "consent_withdrawn_at": iso(cand.consent_withdrawn_at),
        "withdrawn_from": cand.withdrawn_from or [],
        "retention_until": iso(cand.retention_until),
        "applied_at": iso(cand.applied_at),
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
                "pages": d.page_count,
                "chars": d.char_count,
                "error": d.error,
            }
            for d in cand.documents
        ],
        "created_at": iso(cand.created_at),
        "updated_at": iso(cand.updated_at),
    }
    if screenings is not None:
        out["screenings"] = screenings
    return out
