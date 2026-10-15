"""Stages 5-6: verify the LLM profile against the redacted text and derive numbers in code."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from rapidfuzz import fuzz

from app.core.arabic import normalize
from app.llm.schemas import CandidateProfile

SUPERVISION_WORDS = re.compile(r"مشرف|إشراف|اشراف|قائد|رئيس|supervis|lead|manager|head", re.I)


def quote_in_text(quote: str | None, text: str | None, threshold: float = 0.9) -> bool:
    """A quote counts only if it exists (nearly) literally in the redacted text."""
    if not quote or not text:
        return False
    q, t = normalize(quote), normalize(text)
    if len(q) < 8:
        return False
    if q in t:
        return True
    return fuzz.partial_ratio(q, t) / 100.0 >= threshold


def parse_date(value: str | None, now: datetime) -> datetime | None:
    if not value:
        return None
    v = normalize(value)
    if v in ("present", "now", "current", "حتى الان", "الان", "مستمر"):
        return now
    m = re.search(r"(19|20)\d{2}", v)
    if not m:
        return None
    year = int(m.group(0))
    mm = re.search(r"(?:19|20)\d{2}[-/](\d{1,2})", v)
    month = int(mm.group(1)) if mm and 1 <= int(mm.group(1)) <= 12 else 1
    try:
        return datetime(year, month, 1, tzinfo=UTC)
    except ValueError:
        return None


def years_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None:
        return None
    end = end or start
    return round(max(0.0, (end - start).days / 365.25), 1)


@dataclass
class VerifiedProfile:
    data: dict[str, Any]
    derived: dict[str, Any] = field(default_factory=dict)
    dropped: int = 0  # items whose quote was not found


def verify_profile(
    profile: CandidateProfile,
    redacted_text: str,
    threshold: float = 0.9,
    now: datetime | None = None,
) -> VerifiedProfile:
    now = now or datetime.now(UTC)
    kept: dict[str, list[dict[str, Any]]] = {
        k: [] for k in ("experience", "certifications", "skills", "languages", "education")
    }
    dropped = 0
    for section in kept:
        for item in getattr(profile, section):
            if quote_in_text(item.quote, redacted_text, threshold):
                kept[section].append(item.model_dump())
            else:
                dropped += 1
    total_years = 0.0
    sup_years = 0.0
    max_team = 0
    for exp in kept["experience"]:
        s, e = parse_date(exp.get("start"), now), parse_date(exp.get("end"), now)
        if exp.get("end") is None and s is not None:
            e = s  # no end date -> count nothing beyond the start month (never guess)
        y = years_between(s, e)
        exp["years"] = y
        if y:
            total_years += y
            if SUPERVISION_WORDS.search(exp.get("title") or "") or (exp.get("team_size") or 0) > 0:
                sup_years += y
        if exp.get("team_size"):
            max_team = max(max_team, int(exp["team_size"]))
    derived = {
        "total_experience_years": round(total_years, 1),
        "supervision_years": round(sup_years, 1),
        "max_team_size": max_team,
        "valid_certifications": [
            c["name"] for c in kept["certifications"] if c.get("status") == "valid"
        ],
        "expired_or_pending_certifications": [
            c["name"] for c in kept["certifications"] if c.get("status") in ("expired", "pending")
        ],
        "languages": [
            f"{lg['language']}{' (' + lg['level'] + ')' if lg.get('level') else ''}"
            for lg in kept["languages"]
        ],
        "education": [e["level"] for e in kept["education"]],
    }
    data = {**kept, "summary": profile.summary, "derived": derived}
    return VerifiedProfile(data=data, derived=derived, dropped=dropped)
