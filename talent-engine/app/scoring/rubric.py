"""Levels computed in code from structured form answers (number / select / boolean / multiselect)
using the rubric hints. The LLM is used only for free-text answers and for the CV side."""

from __future__ import annotations

from typing import Any

from app.core.arabic import normalize
from app.pipeline.stages.answers import NormalisedAnswer

STRUCTURED_TYPES = {"number", "select", "boolean", "multiselect"}


def has_hints(rubric: list[dict[str, Any]], qtype: str) -> bool:
    if qtype == "number":
        return any(r.get("gte") is not None or r.get("gt") is not None for r in rubric)
    if qtype in ("select", "boolean", "multiselect"):
        return any(r.get("answers") for r in rubric)
    return False


def is_code_judged(criterion: dict[str, Any], question: dict[str, Any] | None) -> bool:
    """True when the criterion's level comes from code: structured question with rubric hints."""
    if question is None:
        return False
    qtype = question.get("type", "text")
    return qtype in STRUCTURED_TYPES and has_hints(criterion.get("rubric", []), qtype)


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
    return 0
