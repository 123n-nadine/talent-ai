"""Stage 2: normalise screening-question answers. Blank ≠ 0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.arabic import normalize

TRUE_WORDS = {"نعم", "yes", "true", "1", "ايوه", "ايوا"}
FALSE_WORDS = {"لا", "no", "false", "0"}


@dataclass
class NormalisedAnswer:
    key: str
    raw: Any
    value: Any
    answered: bool
    canonical: str  # the string an evidence citation must equal


def is_blank(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    if isinstance(v, list | tuple | set | dict) and len(v) == 0:
        return True
    return False


def _to_number(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int | float):
        return float(v)
    s = normalize(str(v)).replace("٫", ".").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def canonical_str(value: Any) -> str:
    if isinstance(value, bool):
        return "نعم" if value else "لا"
    if isinstance(value, int | float):
        return f"{value:g}"
    if isinstance(value, list | tuple):
        return "، ".join(canonical_str(x) for x in value)
    return str(value).strip()


def normalise_one(key: str, qtype: str, raw: Any) -> NormalisedAnswer:
    if is_blank(raw):
        return NormalisedAnswer(key, raw, None, False, "")
    value: Any
    if qtype == "number":
        n = _to_number(raw)
        if n is None:
            return NormalisedAnswer(key, raw, None, False, "")
        value = n
    elif qtype == "multiselect":
        if isinstance(raw, str):
            value = [x.strip() for x in raw.replace("،", ",").split(",") if x.strip()]
        else:
            value = [str(x).strip() for x in raw if not is_blank(x)]
        if not value:
            return NormalisedAnswer(key, raw, None, False, "")
    elif qtype == "boolean":
        if isinstance(raw, bool):
            value = raw
        else:
            w = normalize(str(raw))
            if w in TRUE_WORDS:
                value = True
            elif w in FALSE_WORDS:
                value = False
            else:
                return NormalisedAnswer(key, raw, None, False, "")
    else:
        value = str(raw).strip()
    return NormalisedAnswer(key, raw, value, True, canonical_str(value))


def normalise_answers(
    questions: list[dict[str, Any]], answers: dict[str, Any] | None
) -> dict[str, NormalisedAnswer]:
    answers = answers or {}
    out: dict[str, NormalisedAnswer] = {}
    types = {q["key"]: q.get("type", "text") for q in questions}
    for key, qtype in types.items():
        out[key] = normalise_one(key, qtype, answers.get(key))
    for key, raw in answers.items():  # answers to questions not in the profile are kept as text
        if key not in out:
            out[key] = normalise_one(key, "text", raw)
    return out


def redact_free_text(
    answers: dict[str, NormalisedAnswer], questions: list[dict[str, Any]]
) -> tuple[dict[str, NormalisedAnswer], int]:
    """Free-text answers go through the same redaction as a CV before the model sees them
    (decision 4): an applicant may type a phone, an e-mail, an ID or a date into «describe your
    last job». The redacted string is what the model sees and what its evidence must equal.
    Returns the answers and how many were changed. Final QA, 2026-10-19."""
    from app.redaction.engine import redact

    types = {q["key"]: q.get("type", "text") for q in questions}
    out: dict[str, NormalisedAnswer] = {}
    changed = 0
    for key, a in answers.items():
        if a.answered and types.get(key, "text") == "text" and isinstance(a.value, str):
            r = redact(a.value)
            if r.text != a.value:
                changed += 1
                a = NormalisedAnswer(a.key, a.raw, r.text, True, canonical_str(r.text))
        out[key] = a
    return out, changed
