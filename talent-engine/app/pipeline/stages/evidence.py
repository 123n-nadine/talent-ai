"""Evidence checks (code only). A judgement without verifiable evidence becomes 'missing'.

Form evidence must equal the stored answer; a CV quote must exist in the redacted text.
Answer vs CV contradiction -> the lower level is used and the screening needs review."""

from __future__ import annotations

from app.core.arabic import normalize
from app.llm.base import Judgement
from app.llm.schemas import CriterionJudgement
from app.pipeline.stages.answers import NormalisedAnswer
from app.pipeline.stages.profile import quote_in_text


def _same_value(model_value: str | None, canonical: str) -> bool:
    """The model must be judging the stored answer: equal after normalisation, numerically equal,
    or one contains the other (e.g. '7 سنوات' vs '7')."""
    a, b = normalize(model_value), normalize(canonical)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    try:
        return float(a.replace("،", ".")) == float(b)
    except ValueError:
        return False


def resolve(
    raw: CriterionJudgement,
    answers: dict[str, NormalisedAnswer],
    redacted_text: str | None,
    threshold: float = 0.9,
    question_key: str | None = None,
    code_level: int | None = None,
) -> tuple[Judgement, list[str]]:
    """Return the verified judgement and the problems found (evidence_mismatch, quote_not_found).
    `question_key` is the question that feeds the criterion according to the job (code authority);
    `code_level` is the form level computed in code for structured answers (overrides the model)."""
    problems: list[str] = []
    form_level: int | None = None
    if question_key:
        raw.form_field = question_key
    if code_level is not None:
        form_level = int(code_level)
    elif raw.form_level is not None:
        ans = answers.get(raw.form_field or "")
        if ans is not None and ans.answered and _same_value(raw.form_value, ans.canonical):
            form_level = int(raw.form_level)
        else:
            problems.append("evidence_mismatch")
    cv_level: int | None = None
    if raw.cv_level is not None:
        if quote_in_text(raw.cv_quote, redacted_text, threshold):
            cv_level = int(raw.cv_level)
        else:
            problems.append("quote_not_found")

    if form_level is None and cv_level is None:
        return Judgement(raw.key, 0, None, raw.form_field, None, True, raw.rationale), problems
    contradiction = form_level is not None and cv_level is not None and cv_level < form_level
    if contradiction:
        ans = answers.get(raw.form_field or "")
        evidence = f"{raw.cv_quote} | إجابة النموذج: {ans.canonical if ans else raw.form_value}"
        return Judgement(
            raw.key,
            cv_level or 0,
            "cv_quote",
            raw.form_field,
            evidence,
            False,
            raw.rationale,
            contradiction=True,
            confirmed_by_cv=False,
            form_level=form_level,
            cv_level=cv_level,
            cv_quote=raw.cv_quote,
        ), problems
    if form_level is not None:
        ans = answers[raw.form_field or ""]
        return Judgement(
            raw.key,
            form_level,
            "form_field",
            raw.form_field,
            ans.canonical,
            False,
            raw.rationale,
            confirmed_by_cv=cv_level is not None and cv_level >= form_level,
            form_level=form_level,
            cv_level=cv_level,
            cv_quote=raw.cv_quote if cv_level is not None else None,
        ), problems
    return Judgement(
        raw.key,
        cv_level or 0,
        "cv_quote",
        None,
        raw.cv_quote,
        False,
        raw.rationale,
        form_level=None,
        cv_level=cv_level,
        cv_quote=raw.cv_quote,
    ), problems


def verify_form_evidence(
    j: Judgement, answers: dict[str, NormalisedAnswer]
) -> tuple[Judgement, bool]:
    """Legacy helper kept for the phase-1 tests: re-check a resolved form judgement."""
    if j.missing_evidence or j.source != "form_field":
        return j, False
    ans = answers.get(j.field or "")
    if ans is None or not ans.answered or normalize(j.evidence) != normalize(ans.canonical):
        return Judgement(
            j.key, 0, None, j.field, None, True, "evidence did not match the stored answer"
        ), True
    return j, False
