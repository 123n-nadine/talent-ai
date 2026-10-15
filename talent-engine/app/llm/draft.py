"""Normalise an LLM criteria draft so HR can approve it as is: slug keys, criteria linked to real
question keys, five rubric levels, weights totalling exactly 100. The model only proposes text."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

from app.core.arabic import normalize
from app.domain.models import KEY_RE, LEVELS
from app.llm.base import DraftCriteria
from app.llm.schemas import DraftOutput

QTYPES = {"number", "select", "multiselect", "boolean", "text", "date"}


def _slug(value: str | None, fallback: str, taken: set[str]) -> str:
    v = (value or "").strip().lower()
    v = re.sub(r"[^a-z0-9_]+", "_", v).strip("_")
    if not v or not KEY_RE.match(v) or v[0].isdigit():
        v = fallback
    base, n = v, 2
    while v in taken:
        v = f"{base}_{n}"
        n += 1
    taken.add(v)
    return v


def _match_question(
    ref: str | None, questions: list[dict[str, Any]], originals: dict[str, str]
) -> str | None:
    """Map whatever the model wrote (a key or the question text) to the new question key."""
    if not ref:
        return None
    r = normalize(ref)
    if r in originals:
        return originals[r]
    best, best_score = None, 0.0
    for q in questions:
        score = max(
            fuzz.ratio(r, normalize(q["label"])), fuzz.partial_ratio(r, normalize(q["label"]))
        )
        if score > best_score:
            best, best_score = q["key"], score
    return best if best_score >= 85 else None


def normalise_draft(out: DraftOutput) -> DraftCriteria:
    qtaken: set[str] = set()
    questions: list[dict[str, Any]] = []
    originals: dict[str, str] = {}
    for i, q in enumerate(out.questions):
        d = q.model_dump()
        new_key = _slug(q.key, f"q{i + 1}", qtaken)
        originals[normalize(q.key)] = new_key
        originals[normalize(q.label)] = new_key
        d["key"] = new_key
        d["type"] = d["type"] if d["type"] in QTYPES else "text"
        if d["type"] in ("select", "multiselect") and not d.get("options"):
            d["type"] = "text"
        questions.append(d)

    ctaken: set[str] = set()
    criteria: list[dict[str, Any]] = []
    for i, c in enumerate(out.criteria):
        d = c.model_dump()
        d["text"] = c.text.strip() or (c.key or f"criterion {i + 1}")
        d["key"] = _slug(c.key, f"c{i + 1}", ctaken)
        d["question"] = _match_question(c.question, questions, originals)
        by_level = {int(r.level): r.text for r in c.rubric}
        d["rubric"] = [{"level": lvl, "text": by_level.get(lvl) or "—"} for lvl in LEVELS]
        d["weight"] = max(0.0, float(c.weight))
        criteria.append(d)

    total = sum(item["weight"] for item in criteria) or 1.0
    for item in criteria:
        item["weight"] = round(item["weight"] * 100 / total, 1)
    diff = round(100 - sum(item["weight"] for item in criteria), 1)
    if criteria and diff:
        criteria[0]["weight"] = round(criteria[0]["weight"] + diff, 1)
    return DraftCriteria(
        description=out.description, criteria=criteria, questions=questions, rules=[]
    )
