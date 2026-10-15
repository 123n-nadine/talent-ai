from app.scoring.score import JudgedCriterion, band_for, compute, round1


def row(key, w, lvl, mandatory=False, missing=False, override=None, contradiction=False):
    return JudgedCriterion(
        key=key,
        text=key,
        weight=w,
        mandatory=mandatory,
        level=lvl,
        source=None if missing else "form_field",
        field=key,
        evidence=None if missing else "x",
        missing_evidence=missing,
        contradiction=contradiction,
        overridden_level=override,
    )


def test_worked_example_security_supervisor_81_5():
    rows = [
        row("supervision", 30, 75, True),
        row("security_exp", 20, 100, True),
        row("shifts", 15, 100),
        row("licence", 15, 100),
        row("reports", 8, 50),
        row("first_aid", 7, 0),
        row("languages", 5, 100),
    ]
    r = compute(rows)
    assert r.weighted_sum == 8150
    assert r.score == 81.5
    assert r.coverage == 1.0
    assert r.band == "high"
    assert not r.needs_review
    assert r.raise_score[0] == {
        "criterion": "supervision",
        "text": "supervision",
        "points": 7.5,
        "missing": False,
    }
    assert {x["criterion"]: x["points"] for x in r.raise_score}["first_aid"] == 7.0


def test_client_doc_example_89():
    r = compute([row("a", 40, 90), row("b", 35, 80), row("c", 25, 100)])
    assert r.score == 89.0


def test_bands_at_boundaries():
    assert band_for(49.9) == "low"
    assert band_for(50) == "medium"
    assert band_for(74.9) == "medium"
    assert band_for(75) == "high"


def test_rounding_half_up():
    assert round1(81.45) == 81.5
    assert round1(81.44) == 81.4


def test_mandatory_zero_with_evidence_forces_low_band():
    r = compute([row("m", 20, 0, True), row("x", 80, 100)])
    assert r.score == 80.0
    assert r.band == "low"
    assert "mandatory_zero" in r.flags
    assert not r.needs_review


def test_mandatory_missing_evidence_needs_review_not_low_band():
    r = compute([row("m", 20, 0, True, missing=True), row("x", 80, 100)])
    assert r.score == 80.0
    assert r.coverage == 0.8
    assert r.band == "high"
    assert r.needs_review
    assert {"missing_evidence", "mandatory_missing"} <= set(r.flags)


def test_coverage_threshold_60():
    r = compute([row("a", 59, 100, missing=True), row("b", 41, 100)])
    assert r.coverage == 0.41
    assert r.needs_review and "low_coverage" in r.flags
    r2 = compute([row("a", 40, 100, missing=True), row("b", 60, 100)])
    assert r2.coverage == 0.6 and not r2.needs_review


def test_contradiction_needs_review():
    r = compute([row("a", 100, 50, contradiction=True)])
    assert r.needs_review and "contradiction" in r.flags


def test_override_recomputes_and_counts_as_evidence():
    r = compute([row("a", 50, 0, missing=True, override=100), row("b", 50, 50)])
    assert r.score == 75.0
    assert r.coverage == 1.0
    assert "hr_override" in r.flags and "missing_evidence" not in r.flags


def test_strengths_and_gaps():
    r = compute([row("s", 50, 75), row("g", 30, 25), row("m", 20, 0, missing=True)])
    assert [s["key"] for s in r.strengths] == ["s"]
    assert [g["key"] for g in r.gaps] == ["g", "m"]
    assert r.gaps[1]["missing"] is True
