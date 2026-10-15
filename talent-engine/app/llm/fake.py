"""Deterministic fake provider: derives levels from form answers using the rubric hints.

Used in phase 1 and in all tests, so the pipeline runs without a GPU. It never guesses:
no answer → missing evidence; an answer that matches no hint → level 0 with evidence.
"""

from __future__ import annotations

from typing import Any

from app.core.arabic import normalize
from app.llm.base import DraftCriteria, Judgement, JudgeRequest
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

    def ready(self) -> bool:
        return True

    def judge(self, req: JudgeRequest) -> list[Judgement]:
        out: list[Judgement] = []
        for c in req.criteria:
            qkey = c.get("question")
            q = req.questions.get(qkey) if qkey else None
            ans = req.answers.get(qkey) if qkey else None
            if q is None or ans is None or not ans.answered:
                out.append(Judgement(c["key"], 0, None, qkey, None, missing_evidence=True))
                continue
            lvl = level_from_rubric(c["rubric"], q.get("type", "text"), ans)
            out.append(
                Judgement(
                    key=c["key"],
                    level=lvl,
                    source="form_field",
                    field=qkey,
                    evidence=ans.canonical,
                    missing_evidence=False,
                    rationale="derived from the form answer with the rubric hints",
                )
            )
        return out

    def draft_criteria(self, title: str, description: str) -> DraftCriteria:
        from app.llm.templates import draft_for_title

        return draft_for_title(title, description)
