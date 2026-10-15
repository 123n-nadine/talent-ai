"""Evidence checks (code only). A judgement without verifiable evidence becomes 'missing'."""

from __future__ import annotations

from app.core.arabic import normalize
from app.llm.base import Judgement
from app.pipeline.stages.answers import NormalisedAnswer


def verify_form_evidence(
    j: Judgement, answers: dict[str, NormalisedAnswer]
) -> tuple[Judgement, bool]:
    """Return (possibly corrected judgement, mismatch flag)."""
    if j.missing_evidence:
        return Judgement(j.key, 0, None, j.field, None, True, j.rationale), False
    if j.source != "form_field":
        return j, False
    ans = answers.get(j.field or "")
    if ans is None or not ans.answered or normalize(j.evidence) != normalize(ans.canonical):
        return Judgement(
            j.key, 0, None, j.field, None, True, "evidence did not match the stored answer"
        ), True
    return j, False
