"""Runs the 10-stage pipeline for one screening (ARCHITECTURE §4)."""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.ids import new_id
from app.core.timeutil import utcnow
from app.domain.labels import NO_CV_NOTE
from app.llm.base import JudgeRequest, LLMProvider
from app.llm.registry import get_provider
from app.llm.schemas import CriterionJudgement
from app.pipeline.stages.answers import NormalisedAnswer, normalise_answers
from app.pipeline.stages.evidence import resolve
from app.pipeline.stages.profile import verify_profile
from app.rules.eligibility import evaluate
from app.scoring.rubric import is_code_judged, level_from_rubric
from app.scoring.score import JudgedCriterion, compute, summary_text
from app.services import audit
from app.services.callback import send as send_callback
from app.services.ranking import rank_of
from app.services.screenings import REVIEW_FLAGS, SCORE_FLAGS, to_out
from app.storage.models import CriterionResult, Profile, Screening, Tenant

log = logging.getLogger(__name__)


class StageTracker:
    def __init__(self, stages: list[dict[str, Any]]):
        self.stages = [dict(s) for s in stages]
        self._t0: dict[str, float] = {}

    def start(self, key: str) -> None:
        self._t0[key] = time.time()
        self.set(key, "running")

    def set(self, key: str, status: str, note: str | None = None) -> None:
        for s in self.stages:
            if s["key"] == key:
                s["status"] = status
                s["note"] = note
                if key in self._t0 and status in ("done", "failed", "skipped"):
                    s["ms"] = int((time.time() - self._t0.pop(key)) * 1000)
                return


def _load(db: Session, screening_id: str) -> Screening:
    s = db.get(Screening, screening_id)
    if s is None:
        raise RuntimeError(f"screening {screening_id} not found")
    return s


def run_screening(
    db: Session,
    settings: Settings,
    screening_id: str,
    provider: LLMProvider | None = None,
    deliver: bool = True,
) -> Screening:
    s = _load(db, screening_id)
    if s.status in ("completed", "needs_review"):
        return s
    tenant: Tenant = db.get(Tenant, s.tenant_id)  # type: ignore[assignment]
    s.status = "processing"
    s.started_at = s.started_at or utcnow()
    s.attempts = (s.attempts or 0) + 1
    tracker = StageTracker(s.stages or [])
    db.commit()
    t_start = time.time()

    try:
        prov = provider or get_provider(
            tenant.ai_provider, settings, tenant.ai_model or None, tenant.judge_prompt or None
        )
        version, cand = s.job_version, s.candidate
        tracker.start("intake")
        tracker.set("intake", "done")

        tracker.start("answers")
        answers = normalise_answers(version.questions, cand.answers)
        answered = sum(1 for a in answers.values() if a.answered)
        tracker.set("answers", "done", f"{answered} من {len(version.questions)} إجابات")

        extra_flags = {f for f in (s.flags or []) if f not in SCORE_FLAGS}
        cv = next((d for d in cand.documents if d.kind == "cv"), None)
        redacted_text: str | None = None
        derived: dict[str, Any] = {}
        llm_calls: list[dict[str, Any]] = []
        if cv is None:
            for key in ("cv_text", "redaction", "profile", "evidence_check"):
                tracker.set(key, "skipped", NO_CV_NOTE)
        elif cv.status == "ready":
            note = f"{cv.extraction_method} · {cv.char_count} حرف · {cv.page_count} صفحة"
            if cv.ocr_confidence is not None:
                note += f" · ثقة OCR {round(cv.ocr_confidence * 100)}%"
                if cv.ocr_confidence < settings.ocr_min_confidence:
                    extra_flags.add("low_ocr_confidence")
            tracker.set("cv_text", "done", note)
            counts = (cv.redaction_report or {}).get("counts", {})
            tracker.set(
                "redaction",
                "done",
                "حُذف: " + "، ".join(f"{k} {v}" for k, v in counts.items())
                if counts
                else "لم يُعثر على بيانات شخصية",
            )
            redacted_text = cv.redacted_text or ""
            if prov.name == "fake":
                tracker.set("profile", "skipped", "المزوّد الوهمي لا يقرأ السيرة")
                tracker.set("evidence_check", "skipped", "لا ملف منظّم")
            else:
                tracker.start("profile")
                raw_profile = prov.profile(redacted_text)
                llm_calls.append({"task": "profile", **getattr(prov, "last_usage", {})})
                tracker.start("evidence_check")
                vp = verify_profile(raw_profile, redacted_text, settings.quote_match_threshold)
                derived = vp.derived
                n_items = sum(
                    len(vp.data[k])
                    for k in ("experience", "certifications", "skills", "languages", "education")
                )
                tracker.set("profile", "done", f"{n_items + vp.dropped} عنصر مستخرج")
                tracker.set(
                    "evidence_check",
                    "done",
                    f"{n_items} عنصر بدليل حرفي، {vp.dropped} حُذف لعدم وجود الاقتباس · "
                    f"خبرة {derived['total_experience_years']} سنة · إشراف {derived['supervision_years']} سنة",
                )
                for old_profile in db.query(Profile).filter(Profile.candidate_id == cand.id).all():
                    db.delete(old_profile)
                db.add(
                    Profile(
                        id=new_id("prof"),
                        candidate_id=cand.id,
                        schema_version=settings.profile_schema_version,
                        data=vp.data,
                    )
                )
        else:
            extra_flags.add("cv_unreadable")
            tracker.set(
                "cv_text", "failed", f"ملف السيرة غير مقروء: {cv.error} — التقييم من الإجابات فقط"
            )
            for key in ("redaction", "profile", "evidence_check"):
                tracker.set(key, "skipped", "لا نص للسيرة")

        tracker.start("eligibility")
        elig = evaluate(cand.facts, version.rules)
        tracker.set(
            "eligibility",
            "done",
            {
                "eligible": "مستوفٍ",
                "not_eligible": "غير مستوفٍ بحسب ما كتبه",
                "needs_review": "يحتاج مراجعة",
            }[elig.status],
        )

        tracker.start("judgement")
        questions = {q["key"]: q for q in version.questions}
        # form side: structured answers are judged in code; the model handles free text and the CV
        code_levels: dict[str, int] = {}
        for c in version.criteria:
            q = questions.get(c.get("question") or "")
            ans = answers.get(c.get("question") or "")
            if is_code_judged(c, q) and ans is not None and ans.answered:
                code_levels[c["key"]] = level_from_rubric(c["rubric"], q["type"], ans)  # type: ignore[index]
        needs_model = bool(redacted_text) or any(
            c["key"] not in code_levels
            and (
                answers.get(c.get("question") or "") or NormalisedAnswer("", None, None, False, "")
            ).answered
            for c in version.criteria
        )
        raw_judgements: list[CriterionJudgement] = []
        if needs_model:
            raw_judgements = prov.judge(
                JudgeRequest(
                    criteria=version.criteria,
                    questions=questions,
                    answers=answers,
                    redacted_text=redacted_text,
                    derived=derived,
                    code_levels=code_levels,
                )
            )
            if prov.name != "fake":
                llm_calls.append({"task": "judge", **getattr(prov, "last_usage", {})})
        by_key = {j.key: j for j in raw_judgements}
        rows: list[JudgedCriterion] = []
        problems: list[str] = []
        verified: dict[str, Any] = {}
        for c in version.criteria:
            raw = by_key.get(c["key"])
            if raw is None and c["key"] in code_levels:
                raw = CriterionJudgement(key=c["key"], form_field=c.get("question"))
            if raw is None:
                rows.append(
                    JudgedCriterion(
                        c["key"],
                        c["text"],
                        float(c["weight"]),
                        bool(c["mandatory"]),
                        0,
                        None,
                        c.get("question"),
                        None,
                        missing_evidence=True,
                    )
                )
                continue
            j, probs = resolve(
                raw,
                answers,
                redacted_text,
                settings.quote_match_threshold,
                c.get("question"),
                code_level=code_levels.get(c["key"]),
            )
            problems.extend(probs)
            verified[c["key"]] = j
            rows.append(
                JudgedCriterion(
                    c["key"],
                    c["text"],
                    float(c["weight"]),
                    bool(c["mandatory"]),
                    int(j.level),
                    j.source,
                    j.field,
                    j.evidence,
                    j.missing_evidence,
                    contradiction=j.contradiction,
                    confirmed_by_cv=j.confirmed_by_cv,
                )
            )
        if "evidence_mismatch" in problems:
            extra_flags.add("evidence_mismatch")
        if "quote_not_found" in problems:
            extra_flags.add("quote_not_found")
        n_ev = sum(1 for r in rows if not r.missing_evidence)
        n_cv = sum(1 for r in rows if r.confirmed_by_cv)
        n_contra = sum(1 for r in rows if r.contradiction)
        tracker.set(
            "judgement",
            "done",
            f"{n_ev} معيار بدليل · {len(code_levels)} محسوب بالكود · {n_cv} تؤكده السيرة · {n_contra} تعارض"
            + ("" if needs_model else " · بدون نموذج لغوي"),
        )

        tracker.start("scoring")
        result = compute(rows)
        tracker.set(
            "scoring", "done", f"الدرجة {result.score:g} · التغطية {round(result.coverage * 100)}%"
        )
        tracker.set("index", "skipped", "يُفعَّل مع بنك المتقدمين (المرحلة 8)")

        for old in list(s.criteria):
            db.delete(old)
        for i, r in enumerate(result.rows):
            db.add(
                CriterionResult(
                    id=new_id("cr"),
                    screening_id=s.id,
                    position=i,
                    criterion_key=r.key,
                    text=r.text,
                    weight=r.weight,
                    mandatory=r.mandatory,
                    level=r.level,
                    source=None if r.missing_evidence else r.source,
                    field=r.field,
                    evidence_text=r.evidence,
                    missing_evidence=r.missing_evidence,
                    contradiction=r.contradiction,
                    confirmed_by_cv=r.confirmed_by_cv,
                    form_level=getattr(verified.get(r.key), "form_level", None),
                    cv_level=getattr(verified.get(r.key), "cv_level", None),
                    cv_quote=getattr(verified.get(r.key), "cv_quote", None),
                )
            )
        s.eligibility = elig.status
        s.eligibility_checks = [c.as_dict() for c in elig.checks]
        s.eligibility_reasons = elig.reasons_ar
        s.score = result.score
        s.coverage = result.coverage
        s.band = result.band
        s.flags = sorted(set(result.flags) | extra_flags)
        s.strengths = result.strengths
        s.gaps = result.gaps
        s.raise_score = result.raise_score
        s.summary = summary_text(result, elig.status, elig.reasons_ar)
        s.versions = {
            **(s.versions or {}),
            "provider": prov.name,
            "model": prov.model,
            "prompt": prov.prompt_version,
            "profile_schema": settings.profile_schema_version,
            "llm_calls": llm_calls,
            "total_ms": int((time.time() - t_start) * 1000),
        }
        review = (
            result.needs_review or elig.status == "needs_review" or bool(extra_flags & REVIEW_FLAGS)
        )
        s.needs_review = review
        s.status = "needs_review" if review else "completed"
        s.error = None
        s.completed_at = utcnow()
        s.stages = tracker.stages
        audit.log(
            db,
            tenant.id,
            cand.external_ref,
            "screening." + s.status,
            "system",
            {
                "screening_id": s.id,
                "score": s.score,
                "coverage": s.coverage,
                "band": s.band,
                "eligibility": s.eligibility,
                "flags": s.flags,
                "job_version": version.version,
                "total_ms": s.versions["total_ms"],
            },
        )
        db.commit()
        db.refresh(s)
    except Exception as e:  # noqa: BLE001 - every failure must be recorded on the screening
        db.rollback()
        s = _load(db, screening_id)
        msg = f"{type(e).__name__}: {e}"
        log.error("screening %s attempt %s failed: %s", screening_id, s.attempts, msg)
        log.debug(traceback.format_exc())
        for st in tracker.stages:
            if st["status"] == "running":
                st["status"] = "failed"
        s.stages = tracker.stages
        s.error = msg
        max_attempts = max(1, tenant.max_retries)
        s.status = "failed" if s.attempts >= max_attempts else "queued"
        audit.log(
            db,
            tenant.id,
            s.candidate.external_ref,
            "screening.failed" if s.status == "failed" else "screening.retry_scheduled",
            "system",
            {"screening_id": s.id, "attempt": s.attempts, "error": msg},
        )
        db.commit()
        return s

    if deliver and tenant.callback_url and tenant.callback_secret:
        rank, total = rank_of(db, tenant, s)
        outcome = send_callback(
            tenant.callback_url, tenant.callback_secret, to_out(s, rank, total), settings
        )
        audit.log(
            db,
            tenant.id,
            s.candidate.external_ref,
            "callback.sent" if outcome["ok"] else "callback.failed",
            "system",
            {"screening_id": s.id, **outcome},
        )
        db.commit()
    return s


def execute_with_retries(
    sessionmaker: Any, settings: Settings, screening_id: str, provider: LLMProvider | None = None
) -> str:
    """Run a screening; on engine errors retry with backoff until the tenant's max_retries."""
    backoff = settings.retry_backoff or [0.0]
    status = "queued"
    for i in range(max(1, settings.max_attempts) + 10):
        with sessionmaker() as db:
            s = run_screening(db, settings, screening_id, provider=provider)
            status = s.status
        if status != "queued":
            return status
        time.sleep(backoff[min(i, len(backoff) - 1)])
    return status
