"""Hard eligibility rules: evaluated in code on self-declared facts, never by the LLM.

Outcomes: eligible / not_eligible (as declared) / needs_review (value missing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.arabic import normalize

FACT_LABELS: dict[str, tuple[str, str]] = {
    "nationality": ("الجنسية", "Nationality"),
    "height_cm": ("الطول (سم)", "Height (cm)"),
    "weight_kg": ("الوزن (كجم)", "Weight (kg)"),
    "age": ("العمر", "Age"),
    "gender": ("الجنس", "Gender"),
}
UNITS: dict[str, tuple[str, str]] = {
    "height_cm": ("سم", "cm"),
    "weight_kg": ("كجم", "kg"),
    "age": ("سنة", "years"),
}


@dataclass
class RuleCheck:
    fact: str
    operator: str
    ok: bool | None  # None = value missing
    declared: Any
    required_ar: str
    required_en: str
    text_ar: str
    text_en: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact,
            "operator": self.operator,
            "ok": self.ok,
            "declared": self.declared,
            "required_ar": self.required_ar,
            "required_en": self.required_en,
            "text_ar": self.text_ar,
            "text_en": self.text_en,
        }


@dataclass
class EligibilityResult:
    status: str  # eligible | not_eligible | needs_review
    checks: list[RuleCheck] = field(default_factory=list)

    @property
    def reasons_ar(self) -> list[str]:
        return [c.text_ar for c in self.checks if c.ok is not True]

    @property
    def reasons_en(self) -> list[str]:
        return [c.text_en for c in self.checks if c.ok is not True]


def _label(fact: str) -> tuple[str, str]:
    return FACT_LABELS.get(fact, (fact, fact))


def _unit(fact: str) -> tuple[str, str]:
    return UNITS.get(fact, ("", ""))


def _fmt(fact: str, value: Any, en: bool = False) -> str:
    u = _unit(fact)[1 if en else 0]
    v = (
        f"{value:g}"
        if isinstance(value, int | float) and not isinstance(value, bool)
        else str(value)
    )
    return f"{v} {u}".strip()


def requirement_text(fact: str, operator: str, value: Any) -> tuple[str, str]:
    ua, ue = _unit(fact)
    if operator == "in":
        vals = value if isinstance(value, list) else [value]
        return "ضمن: " + "، ".join(map(str, vals)), "one of: " + ", ".join(map(str, vals))
    if operator == "not_in":
        vals = value if isinstance(value, list) else [value]
        return "ليس ضمن: " + "، ".join(map(str, vals)), "not one of: " + ", ".join(map(str, vals))
    if operator == ">=":
        return f"{_fmt(fact, value)} أو أكثر".strip(), f"{_fmt(fact, value, True)} or more".strip()
    if operator == "<=":
        return f"{_fmt(fact, value)} أو أقل".strip(), f"{_fmt(fact, value, True)} or less".strip()
    if operator == ">":
        return f"أكثر من {_fmt(fact, value)}", f"more than {_fmt(fact, value, True)}"
    if operator == "<":
        return f"أقل من {_fmt(fact, value)}", f"less than {_fmt(fact, value, True)}"
    if operator == "between":
        lo, hi = value
        return (
            f"من {_fmt(fact, lo)} إلى {_fmt(fact, hi)}",
            f"between {_fmt(fact, lo, True)} and {_fmt(fact, hi, True)}",
        )
    if operator == "!=":
        return f"غير {value}", f"not {value}"
    return f"{_fmt(fact, value)}", f"{_fmt(fact, value, True)}"


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _num(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    return float(normalize(str(value)))


OPERATORS: tuple[str, ...] = ("in", "not_in", ">=", "<=", ">", "<", "==", "!=", "between")


class UnknownOperator(ValueError):
    pass


def check_value(value: Any, operator: str, expected: Any) -> bool:
    if operator not in OPERATORS:
        raise UnknownOperator(f"unknown rule operator '{operator}'")
    if operator in ("in", "not_in"):
        options = expected if isinstance(expected, list) else [expected]
        hit = any(normalize(str(value)) == normalize(str(o)) for o in options)
        return hit if operator == "in" else not hit
    if operator == "==":
        try:
            return _num(value) == _num(expected)
        except ValueError:
            return normalize(str(value)) == normalize(str(expected))
    if operator == "!=":
        try:
            return _num(value) != _num(expected)
        except ValueError:
            return normalize(str(value)) != normalize(str(expected))
    if operator == "between":
        if not isinstance(expected, list | tuple) or len(expected) != 2:
            raise ValueError("'between' needs a [low, high] pair")
        lo, hi = expected
        return _num(lo) <= _num(value) <= _num(hi)
    v, e = _num(value), _num(expected)
    return {">=": v >= e, "<=": v <= e, ">": v > e, "<": v < e}[operator]


def evaluate(facts: dict[str, Any] | None, rules: list[dict[str, Any]]) -> EligibilityResult:
    facts = facts or {}
    checks: list[RuleCheck] = []
    failed = False
    missing = False
    for r in rules:
        fact, op, expected = r["fact"], r["operator"], r.get("value")
        if op not in OPERATORS:
            raise UnknownOperator(f"unknown rule operator '{op}' on fact '{fact}'")
        la, le = _label(fact)
        ra, re_ = requirement_text(fact, op, expected)
        value = facts.get(fact)
        if _is_missing(value):
            missing = True
            checks.append(
                RuleCheck(
                    fact,
                    op,
                    None,
                    None,
                    ra,
                    re_,
                    f"{la}: غير مصرّح به (المطلوب {ra}) — يحتاج مراجعة",
                    f"{le}: not declared (required {re_}) — needs review",
                )
            )
            continue
        try:
            ok = check_value(value, op, expected)
        except (ValueError, TypeError):
            ok = False
        if not ok:
            failed = True
        checks.append(
            RuleCheck(
                fact,
                op,
                ok,
                value,
                ra,
                re_,
                f"{la}: المصرّح به {_fmt(fact, value)} — المطلوب {ra}",
                f"{le}: declared {_fmt(fact, value, True)} — required {re_}",
            )
        )
    status = "not_eligible" if failed else "needs_review" if missing else "eligible"
    return EligibilityResult(status=status, checks=checks)
