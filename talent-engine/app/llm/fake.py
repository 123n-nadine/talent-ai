"""Deterministic fake provider: derives levels from form answers using the rubric hints.

Used in phase 1 and in tests, so the pipeline runs without a GPU. It never guesses:
no answer → no form level; an answer that matches no hint → level 0 with evidence.
Optional `cv_levels` (criterion key -> (level, quote)) lets tests exercise the CV path.
"""

from __future__ import annotations

from typing import Any

from app.core.arabic import normalize
from app.llm.base import DraftCriteria, JudgeRequest
from app.llm.schemas import CandidateProfile, CriterionJudgement
from app.pipeline.stages.answers import NormalisedAnswer


def level_from_rubric(rubric: list[dict[str, Any]], qtype: str, answer: NormalisedAnswer) -> int:
    levels = sorted(rubric, key=lambda r: -int(r["level"]))
    value = answer.value
    if qtype == "number":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0
        for r in levels:
            gte, gt = r.get("gte"), r.get("gt")
            if (gte is not None and v >= float(gte)) or (gt is not None and v > float(gt)):
                return int(r["level"])
        return 0
    if qtype == "multiselect":
        selected = {normalize(x) for x in (value if isinstance(value, list) else [value])}
        for r in levels:
            opts = r.get("answers") or []
            if opts and {normalize(o) for o in opts} <= selected:
                return int(r["level"])
        return 0
    if qtype in ("select", "boolean"):
        word = normalize("نعم" if value is True else "لا" if value is False else str(value))
        for r in levels:
            opts = r.get("answers") or []
            if any(normalize(o) == word for o in opts):
                return int(r["level"])
        return 0
    return 0  # text/date: the fake provider cannot judge free text


class FakeLLM:
    name = "fake"
    model = "fake-rubric-v1"
    prompt_version = "judge-fake-v1"

    def __init__(self, cv_levels: dict[str, tuple[int, str]] | None = None):
        self.cv_levels = cv_levels or {}

    def ready(self) -> bool:
        return True

    def profile(self, redacted_text: str) -> CandidateProfile:
        return CandidateProfile(summary="")

    def judge(self, req: JudgeRequest) -> list[CriterionJudgement]:
        out: list[CriterionJudgement] = []
        for c in req.criteria:
            qkey = c.get("question")
            q = req.questions.get(qkey) if qkey else None
            ans = req.answers.get(qkey) if qkey else None
            j = CriterionJudgement(key=c["key"], form_field=qkey)
            if q is not None and ans is not None and ans.answered:
                j.form_level = level_from_rubric(c["rubric"], q.get("type", "text"), ans)  # type: ignore[assignment]
                j.form_value = ans.canonical
                j.rationale = "مشتق من إجابة النموذج وفق الرُّبرِك"
            if c["key"] in self.cv_levels and req.redacted_text:
                lvl, quote = self.cv_levels[c["key"]]
                j.cv_level, j.cv_quote = lvl, quote  # type: ignore[assignment]
            out.append(j)
        return out

    def draft_criteria(self, title: str, description: str) -> DraftCriteria:
        from app.llm.templates import draft_for_title

        return draft_for_title(title, description)
