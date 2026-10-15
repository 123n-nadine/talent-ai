"""Deterministic fake provider: derives levels from form answers using the rubric hints.

Used in phase 1 and in tests, so the pipeline runs without a GPU. It never guesses:
no answer → no form level; an answer that matches no hint → level 0 with evidence.
Optional `cv_levels` (criterion key -> (level, quote)) lets tests exercise the CV path.
"""

from __future__ import annotations

from app.llm.base import DraftCriteria, JudgeRequest
from app.llm.schemas import CandidateProfile, CriterionJudgement
from app.scoring.rubric import level_from_rubric


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
