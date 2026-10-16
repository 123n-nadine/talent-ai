"""Impact preview: what approving new criteria/weights would do to the current applicants.

Levels already judged are kept (the LLM is not called); only weights, mandatory flags and the set
of criteria change. A criterion that is new for an applicant counts as missing evidence."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.scoring.score import JudgedCriterion, compute
from app.services.ranking import build_ranking
from app.services.screenings import REVIEW_FLAGS, latest_per_candidate
from app.storage.models import Job, Tenant


def preview(
    db: Session, tenant: Tenant, job: Job, criteria: list[dict[str, Any]]
) -> dict[str, Any]:
    current = build_ranking(db, tenant, job)
    old_rank = {x["candidate_ref"]: x["rank"] for x in current["ranked"]}
    rows: list[dict[str, Any]] = []
    for s in latest_per_candidate(db, job):
        if s.status not in ("completed", "needs_review"):
            continue
        by_key = {r.criterion_key: r for r in s.criteria}
        judged: list[JudgedCriterion] = []
        for c in criteria:
            r = by_key.get(c["key"])
            weight, mandatory = float(c.get("weight") or 0), bool(c.get("mandatory"))
            if r is None:
                judged.append(
                    JudgedCriterion(
                        c["key"],
                        c.get("text") or c["key"],
                        weight,
                        mandatory,
                        0,
                        missing_evidence=True,
                    )
                )
                continue
            judged.append(
                JudgedCriterion(
                    r.criterion_key,
                    c.get("text") or r.text,
                    weight,
                    mandatory,
                    r.level,
                    source=r.source if r.source != "hr_override" else "form_field",
                    field=r.field,
                    evidence=r.evidence_text,
                    missing_evidence=r.missing_evidence,
                    contradiction=r.contradiction,
                    confirmed_by_cv=r.confirmed_by_cv,
                    overridden_level=r.overridden_level,
                )
            )
        res = compute(judged)
        review = (
            res.needs_review
            or s.eligibility == "needs_review"
            or bool(set(s.flags or []) & REVIEW_FLAGS)
        )
        rankable = s.eligibility == "eligible" and not s.duplicate_of and not review
        rows.append(
            {
                "candidate_ref": s.candidate.external_ref,
                "screening_id": s.id,
                "old_score": s.score,
                "new_score": res.score,
                "old_band": s.band,
                "new_band": res.band,
                "old_rank": old_rank.get(s.candidate.external_ref),
                "eligibility": s.eligibility,
                "rankable": rankable,
                "needs_review": review,
            }
        )
    ranked = sorted(
        (x for x in rows if x["rankable"]),
        key=lambda x: (-(x["new_score"] or 0), x["candidate_ref"]),
    )
    for i, row in enumerate(ranked):
        row["new_rank"] = i + 1
    for row in rows:
        row.setdefault("new_rank", None)
        row["delta"] = round((row["new_score"] or 0) - (row["old_score"] or 0), 1)
        row["band_changed"] = row["old_band"] != row["new_band"]
        row["rank_changed"] = row["old_rank"] != row["new_rank"]
    rows.sort(key=lambda x: (x["new_rank"] is None, x["new_rank"] or 0, -(x["new_score"] or 0)))
    return {
        "job_ref": job.external_ref,
        "job_version": job.active_version,
        "rows": rows,
        "summary": {
            "applicants": len(rows),
            "score_changed": sum(1 for x in rows if abs(x["delta"]) > 0.05),
            "band_changed": sum(1 for x in rows if x["band_changed"]),
            "rank_changed": sum(1 for x in rows if x["rank_changed"]),
        },
        "weights_total": round(sum(float(c.get("weight") or 0) for c in criteria), 1),
    }
