"""Talent pool (client feature 13): suggest past applicants for a new opening.

Order of decisions (ARCHITECTURE §8): hard rules first (code, on the declared facts), then semantic
similarity between the opening and the applicant's verified profile. Applicants who withdrew
consent, whose retention period ended or who already applied to the opening are never suggested;
they are listed as excluded with the reason. Suggestions only: nothing is moved or changed."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.embeddings.base import EmbeddingProvider, as_query, cosine
from app.rules.eligibility import evaluate
from app.services import audit
from app.storage.models import Candidate, Document, Embedding, Job, JobVersion, Screening, Tenant

STRUCTURED = {"number", "select", "multiselect", "boolean", "date"}
EXCLUDED_LABELS = {
    "consent_withdrawn": ("سحب موافقته على المعالجة", "withdrew consent to processing"),
    "retention_expired": ("انتهت مدة الاحتفاظ ببياناته", "retention period ended"),
    "already_applied": ("تقدّم لهذا الشاغر بالفعل", "already applied to this opening"),
    "not_eligible": ("غير مستوفٍ للشروط الإلزامية", "does not meet the hard rules"),
    "duplicate": ("طلب أحدث لنفس الشخص موجود", "a newer application of the same person exists"),
}


def _aware(dt):
    from datetime import UTC

    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=UTC)


def indexable(cand: Candidate) -> tuple[bool, str | None]:
    if not cand.consent:
        return False, "consent_withdrawn"
    if cand.retention_until is not None and _aware(cand.retention_until) < utcnow():
        return False, "retention_expired"
    return True, None


def profile_text(
    s: Screening, version: JobVersion, rows: list[Any], cv_text: str | None, cv_chars: int
) -> str:
    """What the applicant showed, without identity: levelled criteria with their evidence, the
    structured answers and the start of the redacted CV."""
    questions = {q["key"]: q for q in version.questions or []}
    lines = [f"تقدّم لوظيفة: {s.job.title}"]
    for r in rows:
        level = r.overridden_level if r.overridden_level is not None else r.level
        if level and level > 0:
            ev = r.evidence or ""
            lines.append(f"{r.text}: المستوى {level}" + (f" — {ev[:160]}" if ev else ""))
    for key, value in (s.candidate.answers or {}).items():
        q = questions.get(key)
        if not q or q.get("type") not in STRUCTURED or value in (None, "", []):
            continue
        shown = "، ".join(map(str, value)) if isinstance(value, list) else str(value)
        lines.append(f"{q.get('label', key)}: {shown}")
    if cv_text:
        lines.append("السيرة: " + " ".join(cv_text.split())[:cv_chars])
    return "\n".join(lines)


def job_text(job: Job, version: JobVersion) -> str:
    parts = [f"الوظيفة: {job.title}", job.description or ""]
    for c in version.criteria or []:
        top = next(
            (r.get("text") for r in c.get("rubric", []) if int(r.get("level", 0)) == 100), ""
        )
        parts.append(f"{c['text']} ({c['weight']:g}%)" + (f": {top}" if top and top != "—" else ""))
    return "\n".join(p for p in parts if p)


def index_screening(
    db: Session,
    provider: EmbeddingProvider,
    s: Screening,
    version: JobVersion,
    rows: list[Any],
    cv_chars: int = 1500,
) -> tuple[str, str]:
    """Store the profile embedding of a finished screening. Returns a short stage note (ar, en)."""
    cand = s.candidate
    ok, why = indexable(cand)
    if not ok:
        db.execute(delete(Embedding).where(Embedding.candidate_id == cand.id))
        ar, en = EXCLUDED_LABELS[why or "consent_withdrawn"]
        return f"{ar} — لا فهرسة", f"{en} — not indexed"
    doc = db.scalar(
        select(Document)
        .where(Document.candidate_id == cand.id, Document.status == "ready")
        .limit(1)
    )
    text = profile_text(s, version, rows, doc.redacted_text if doc else None, cv_chars)
    digest = hashlib.sha256(text.encode()).hexdigest()
    existing = db.scalar(select(Embedding).where(Embedding.candidate_id == cand.id).limit(1))
    if existing is not None and existing.text_hash == digest and existing.model == provider.model:
        existing.screening_id = s.id
        return "الملف مفهرس مسبقًا", "profile already indexed"
    vector = provider.embed([text])[0]
    db.execute(delete(Embedding).where(Embedding.candidate_id == cand.id))
    db.add(
        Embedding(
            id=new_id("emb"),
            candidate_id=cand.id,
            model=provider.model,
            vector=vector,
            screening_id=s.id,
            text_hash=digest,
        )
    )
    return "أُضيف لبنك المتقدمين", "added to the talent pool"


def _latest_completed(db: Session, cand: Candidate) -> Screening | None:
    return db.scalar(
        select(Screening)
        .where(
            Screening.candidate_id == cand.id, Screening.status.in_(("completed", "needs_review"))
        )
        .order_by(Screening.completed_at.desc())
        .limit(1)
    )


def search(
    db: Session,
    tenant: Tenant,
    job: Job,
    version: JobVersion,
    provider: EmbeddingProvider,
    limit: int = 20,
    actor: str = "adapter",
) -> dict[str, Any]:
    applied = set(db.scalars(select(Screening.candidate_id).where(Screening.job_id == job.id)))
    cands = db.scalars(select(Candidate).where(Candidate.tenant_id == tenant.id)).all()
    embeddings = {
        e.candidate_id: e
        for e in db.scalars(
            select(Embedding).join(Candidate).where(Candidate.tenant_id == tenant.id)
        )
    }
    # one person, one suggestion: keep the newest application per national-ID token
    newest: dict[str, Candidate] = {}
    for c in cands:
        if c.id_token:
            k = c.id_token
            if k not in newest or (_aware(c.applied_at or c.created_at), c.external_ref) > (
                _aware(newest[k].applied_at or newest[k].created_at),
                newest[k].external_ref,
            ):
                newest[k] = c
    qvec = provider.embed([as_query(job_text(job, version))])[0]
    suggestions: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    def exclude(
        c: Candidate, code: str, detail: list[str] | None = None, prev: Screening | None = None
    ) -> None:
        ar, en = EXCLUDED_LABELS[code]
        excluded.append(
            {
                "candidate_ref": c.external_ref,
                "reason": code,
                "reason_ar": ar,
                "reason_en": en,
                "details": detail or [],
                "previous_job_ref": prev.job.external_ref if prev else None,
            }
        )

    for c in cands:
        prev = _latest_completed(db, c)
        if prev is None:
            continue  # never screened: nothing verified to compare
        if c.id in applied:
            exclude(c, "already_applied", prev=prev)
            continue
        ok, why = indexable(c)
        if not ok:
            exclude(c, why or "consent_withdrawn", prev=prev)
            continue
        if c.id_token and newest.get(c.id_token) is not c:
            exclude(c, "duplicate", prev=prev)
            continue
        elig = evaluate(c.facts or {}, version.rules or [])
        if elig.status == "not_eligible":
            exclude(c, "not_eligible", elig.reasons_ar, prev=prev)
            continue
        emb = embeddings.get(c.id)
        if emb is None:
            continue
        sim = max(0.0, cosine(qvec, list(emb.vector)))
        suggestions.append(
            {
                "candidate_ref": c.external_ref,
                "similarity": round(sim, 4),
                "eligibility": elig.status,
                "eligibility_checks": [ch.__dict__ for ch in elig.checks],
                "previous": {
                    "job_ref": prev.job.external_ref,
                    "job_title": prev.job.title,
                    "score": prev.score,
                    "band": prev.band,
                    "status": prev.status,
                    "completed_at": iso(prev.completed_at),
                    "strengths": [x.get("text") for x in (prev.strengths or [])][:4],
                },
                "applied_at": iso(c.applied_at),
                "retention_until": iso(c.retention_until),
            }
        )
    suggestions.sort(
        key=lambda x: (x["eligibility"] != "eligible", -x["similarity"], x["candidate_ref"])
    )
    audit.log(
        db,
        tenant.id,
        job.external_ref,
        "talent_pool.searched",
        actor,
        {"suggested": len(suggestions[:limit]), "excluded": len(excluded), "model": provider.model},
    )
    return {
        "job_ref": job.external_ref,
        "job_version": version.version,
        "model": provider.model,
        "suggestion_only": True,
        "note_ar": "اقتراح فقط: لا يُنقل أحد ولا تتغيّر حالة أي طلب تلقائيًا. الشروط الإلزامية أولًا ثم التشابه.",
        "suggestions": suggestions[:limit],
        "excluded": excluded,
        "counts": {
            "suggested": len(suggestions[:limit]),
            "eligible_matches": len(suggestions),
            "excluded": len(excluded),
        },
    }


def reindex(
    db: Session, tenant: Tenant, provider: EmbeddingProvider, cv_chars: int = 1500
) -> dict[str, int]:
    """Index the latest finished screening of every candidate (existing data, model change)."""
    from app.services.screenings import rows_from_results

    done = skipped = 0
    for c in db.scalars(select(Candidate).where(Candidate.tenant_id == tenant.id)).all():
        s = _latest_completed(db, c)
        if s is None:
            continue
        note, _ = index_screening(
            db, provider, s, s.job_version, rows_from_results(list(s.criteria)), cv_chars
        )
        ok = note.startswith("أُضيف") or note.startswith("الملف")
        done += ok
        skipped += not ok
    db.flush()
    return {"indexed": done, "skipped": skipped}
