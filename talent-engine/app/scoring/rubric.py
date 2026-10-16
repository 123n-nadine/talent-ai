"""Levels computed in code from structured form answers (number / select / boolean / multiselect)
using the rubric hints. The LLM is used only for free-text answers and for the CV side."""

from __future__ import annotations

import re
from typing import Any

from app.core.arabic import normalize
from app.pipeline.stages.answers import NormalisedAnswer

STRUCTURED_TYPES = {"number", "select", "boolean", "multiselect"}

# Arabic / English number words for durations ("سنتين", "ثلاث سنوات", "two years")
_UNIT = r"(?:سنة|سنه|سنوات|سنين|عام|أعوام|اعوام|years?|yrs?)"
_DUAL = {"سنتين": 2.0, "سنتان": 2.0, "عامين": 2.0, "عامان": 2.0}
_WORDS = {
    "نصف": 0.5,
    "واحدة": 1,
    "واحد": 1,
    "ثلاث": 3,
    "ثلاثة": 3,
    "أربع": 4,
    "اربع": 4,
    "أربعة": 4,
    "اربعة": 4,
    "خمس": 5,
    "خمسة": 5,
    "ست": 6,
    "ستة": 6,
    "سبع": 7,
    "سبعة": 7,
    "ثماني": 8,
    "ثمان": 8,
    "ثمانية": 8,
    "تسع": 9,
    "تسعة": 9,
    "عشر": 10,
    "عشرة": 10,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "half": 0.5,
}
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def years_in_quote(text: str | None) -> float | None:
    """Number of years stated in a CV quote, read in code (decision 6: the LLM judges, code
    computes). Handles digits next to a unit even when PDF extraction moved them ("أمنية7. سنوات"),
    Arabic duals ("سنتين") and number words ("ثلاث سنوات", "two years"). None when no duration."""
    if not text:
        return None
    t = text.translate(_DIGITS)
    for w, n in _DUAL.items():
        if w in t:
            return n
    m = re.search(rf"(\d+(?:[.,]\d+)?)\s*\+?[\s.،,]*{_UNIT}", t, flags=re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.search(rf"(\w+)\s+{_UNIT}", t, flags=re.IGNORECASE)
    if m and m.group(1).lower() in _WORDS:
        return float(_WORDS[m.group(1).lower()])
    if re.search(r"(?:لمدة|مدة)\s+(?:سنة|عام)\b", t):
        return 1.0
    return None


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
