from app.rules.eligibility import evaluate, requirement_text

RULES = [
    {"fact": "nationality", "operator": "in", "value": ["السعودية"]},
    {"fact": "height_cm", "operator": ">=", "value": 180},
    {"fact": "weight_kg", "operator": "<=", "value": 80},
    {"fact": "age", "operator": ">=", "value": 18},
]


def test_eligible():
    r = evaluate({"nationality": "السعودية", "height_cm": 183, "weight_kg": 78, "age": 34}, RULES)
    assert r.status == "eligible"
    assert r.reasons_ar == []
    assert all(c.ok for c in r.checks)


def test_not_eligible_as_declared_height():
    r = evaluate({"nationality": "السعودية", "height_cm": 172, "weight_kg": 70, "age": 32}, RULES)
    assert r.status == "not_eligible"
    assert r.reasons_ar == ["الطول (سم): المصرّح به 172 سم — المطلوب 180 سم أو أكثر"]


def test_not_eligible_nationality_beats_missing():
    r = evaluate({"nationality": "مصر", "height_cm": None, "weight_kg": 79, "age": 36}, RULES)
    assert r.status == "not_eligible"
    assert any("الجنسية" in t for t in r.reasons_ar)


def test_missing_value_needs_review():
    r = evaluate({"nationality": "السعودية", "height_cm": None, "weight_kg": 78, "age": 38}, RULES)
    assert r.status == "needs_review"
    assert r.reasons_ar == ["الطول (سم): غير مصرّح به (المطلوب 180 سم أو أكثر) — يحتاج مراجعة"]


def test_arabic_normalisation_and_digits():
    r = evaluate(
        {"nationality": "السعوديه", "height_cm": "١٨٣", "weight_kg": "80", "age": 20}, RULES
    )
    assert r.status == "eligible"


def test_requirement_sentences():
    assert requirement_text("height_cm", ">=", 180) == ("180 سم أو أكثر", "180 cm or more")
    assert requirement_text("weight_kg", "<=", 80) == ("80 كجم أو أقل", "80 kg or less")
    assert requirement_text("age", "between", [18, 45]) == (
        "من 18 سنة إلى 45 سنة",
        "between 18 years and 45 years",
    )
    assert requirement_text("nationality", "in", ["السعودية"]) == (
        "ضمن: السعودية",
        "one of: السعودية",
    )


def test_no_rules_is_eligible():
    assert evaluate({}, []).status == "eligible"
