"""Scoring (ARCHITECTURE §5). The LLM judges levels; everything here is computed in code.

score = Σ(weight% × level) / 100, coverage = Σ weight with evidence, bands high ≥ 75,
medium 50–74.9, low < 50. Mandatory criterion at level 0 WITH evidence → band low.
Mandatory criterion with MISSING evidence, coverage < 60% or a contradiction → needs review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.domain.labels import BANDS, FLAGS


@dataclass
class JudgedCriterion:
    key: str
    text: str
    weight: float
    mandatory: bool
    level: int
    source: str | None = None  # form_field | cv_quote | None
    field: str | None = None
    evidence: str | None = None
    missing_evidence: bool = False
    contradiction: bool = False
    confirmed_by_cv: bool = False
    overridden_level: int | None = None
    override_reason: str | None = None
    override_by: str | None = None


@dataclass
class ScoredCriterion:
    key: str
    text: str
    weight: float
    mandatory: bool
    level: int
    effective_level: int
    has_evidence: bool
    points: float
    source: str | None
    field: str | None
    evidence: str | None
    missing_evidence: bool
    contradiction: bool
    confirmed_by_cv: bool
    overridden_level: int | None
    override_reason: str | None
    override_by: str | None


@dataclass
class ScoreResult:
    score: float
    coverage: float
    band: str
    needs_review: bool
    mandatory_zero: bool
    flags: list[str]
    rows: list[ScoredCriterion]
    strengths: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    raise_score: list[dict[str, Any]] = field(default_factory=list)
    weighted_sum: float = 0.0


def round1(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def band_for(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def compute(rows: list[JudgedCriterion], review_threshold: float = 0.6) -> ScoreResult:
    total_w = sum(r.weight for r in rows)
    weighted = 0.0
    covered = 0.0
    flags: set[str] = set()
    needs_review = False
    mandatory_zero = False
    scored: list[ScoredCriterion] = []

    for r in rows:
        overridden = r.overridden_level is not None
        has_evidence = (not r.missing_evidence) or overridden
        if overridden:
            lvl = int(r.overridden_level or 0)
        elif r.missing_evidence:
            lvl = 0
        else:
            lvl = int(r.level)
        weighted += r.weight * lvl
        if has_evidence:
            covered += r.weight
        if r.missing_evidence and not overridden:
            flags.add("missing_evidence")
            if r.mandatory:
                flags.add("mandatory_missing")
                needs_review = True
        if r.contradiction:
            flags.add("contradiction")
            needs_review = True
        if r.mandatory and has_evidence and lvl == 0:
            mandatory_zero = True
            flags.add("mandatory_zero")
        if overridden:
            flags.add("hr_override")
        scored.append(
            ScoredCriterion(
                key=r.key,
                text=r.text,
                weight=r.weight,
                mandatory=r.mandatory,
                level=int(r.level),
                effective_level=lvl,
                has_evidence=has_evidence,
                points=round1(r.weight * lvl / 100),
                source="hr_override" if overridden else r.source,
                field=r.field,
                evidence=r.evidence,
                missing_evidence=r.missing_evidence,
                contradiction=r.contradiction,
                confirmed_by_cv=r.confirmed_by_cv,
                overridden_level=r.overridden_level,
                override_reason=r.override_reason,
                override_by=r.override_by,
            )
        )

    score = round1(weighted / total_w) if total_w else 0.0
    coverage = round(covered / total_w, 4) if total_w else 0.0
    band = "low" if mandatory_zero else band_for(score)
    if coverage < review_threshold:
        flags.add("low_coverage")
        needs_review = True

    strengths = [
        {"key": s.key, "text": s.text, "level": s.effective_level}
        for s in scored
        if s.has_evidence and s.effective_level >= 75
    ]
    gaps = [
        {
            "key": s.key,
            "text": s.text,
            "level": s.effective_level,
            "missing": s.missing_evidence and s.overridden_level is None,
        }
        for s in scored
        if (s.missing_evidence and s.overridden_level is None) or s.effective_level <= 25
    ]
    raise_score = sorted(
        (
            {
                "criterion": s.key,
                "text": s.text,
                "points": round1(s.weight * (100 - s.effective_level) / 100),
                "missing": s.missing_evidence and s.overridden_level is None,
            }
            for s in scored
            if s.effective_level < 100
        ),
        key=lambda x: (-float(str(x["points"])), str(x["criterion"])),
    )
    return ScoreResult(
        score=score,
        coverage=coverage,
        band=band,
        needs_review=needs_review,
        mandatory_zero=mandatory_zero,
        flags=sorted(flags),
        rows=scored,
        strengths=strengths,
        gaps=gaps,
        raise_score=raise_score,
        weighted_sum=weighted,
    )


def summary_text(
    result: ScoreResult, eligibility_status: str, eligibility_reasons: list[str]
) -> str:
    """Arabic summary computed from the numbers (no LLM in phase 1)."""
    band_ar = BANDS[result.band][0]
    parts = [
        f"الدرجة {result.score:g} من 100 (الفئة: {band_ar})، التغطية {round(result.coverage * 100)}%."
    ]
    if eligibility_status == "not_eligible":
        parts.append(
            "غير مستوفٍ للشروط الإلزامية بحسب ما كتبه: " + "؛ ".join(eligibility_reasons) + "."
        )
    elif eligibility_status == "needs_review":
        parts.append("شرط إلزامي بلا قيمة مصرّح بها: " + "؛ ".join(eligibility_reasons) + ".")
    else:
        parts.append("مستوفٍ للشروط الإلزامية بحسب ما كتبه.")
    if result.strengths:
        parts.append("نقاط القوة: " + "، ".join(s["text"] for s in result.strengths) + ".")
    if result.gaps:
        parts.append("النواقص: " + "، ".join(g["text"] for g in result.gaps) + ".")
    for f in result.flags:
        if f in ("mandatory_missing", "low_coverage", "contradiction", "mandatory_zero"):
            parts.append(FLAGS[f][0] + ".")
    if result.needs_review:
        parts.append("يحتاج مراجعة بشرية قبل أي قرار.")
    return " ".join(parts)
