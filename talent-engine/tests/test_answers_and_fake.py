from app.llm.base import JudgeRequest
from app.llm.fake import FakeLLM, level_from_rubric
from app.llm.templates import LANG_RUBRIC, SEC_QUESTIONS, SEC_SUPERVISOR_CRITERIA, YEARS_RUBRIC
from app.pipeline.stages.answers import normalise_answers, normalise_one
from app.pipeline.stages.evidence import resolve, verify_form_evidence

Q = {q["key"]: q for q in SEC_QUESTIONS}


def test_blank_is_not_answered_and_zero_is_an_answer():
    assert normalise_one("y", "number", "").answered is False
    assert normalise_one("y", "number", None).answered is False
    assert normalise_one("l", "multiselect", []).answered is False
    z = normalise_one("y", "number", 0)
    assert z.answered and z.value == 0.0 and z.canonical == "0"
    a = normalise_one("y", "number", "٤")
    assert a.answered and a.value == 4.0 and a.canonical == "4"


def test_years_rubric_thresholds_match_demo():
    cases = {0: 0, 0.5: 25, 1: 50, 2: 50, 3: 75, 5: 75, 6: 100}
    for years, expected in cases.items():
        assert (
            level_from_rubric(YEARS_RUBRIC, "number", normalise_one("y", "number", years))
            == expected
        )


def test_language_rubric():
    assert (
        level_from_rubric(
            LANG_RUBRIC, "multiselect", normalise_one("l", "multiselect", ["العربية", "الإنجليزية"])
        )
        == 100
    )
    assert (
        level_from_rubric(
            LANG_RUBRIC, "multiselect", normalise_one("l", "multiselect", ["العربية"])
        )
        == 50
    )
    assert (
        level_from_rubric(
            LANG_RUBRIC, "multiselect", normalise_one("l", "multiselect", ["الإنجليزية"])
        )
        == 0
    )


def test_fake_judge_is_deterministic_and_cites_the_stored_answer():
    answers = {
        "years_sup": 4,
        "years_sec": 6,
        "shifts": "أعددتها بنفسي",
        "licence": "سارية",
        "reports": "أحيانًا",
        "first_aid": "لا",
        "languages": ["العربية", "الإنجليزية"],
    }
    norm = normalise_answers(SEC_QUESTIONS, answers)
    req = JudgeRequest(criteria=SEC_SUPERVISOR_CRITERIA, questions=Q, answers=norm)
    j1 = [resolve(r, norm, None)[0] for r in FakeLLM().judge(req)]
    j2 = [resolve(r, norm, None)[0] for r in FakeLLM().judge(req)]
    assert [(j.key, j.level) for j in j1] == [(j.key, j.level) for j in j2]
    levels = {j.key: j.level for j in j1}
    assert levels == {
        "supervision": 75,
        "security_exp": 100,
        "shifts": 100,
        "licence": 100,
        "reports": 50,
        "first_aid": 0,
        "languages": 100,
    }
    for j in j1:
        fixed, mismatch = verify_form_evidence(j, norm)
        assert not mismatch and fixed.evidence == norm[j.field].canonical


def test_missing_answer_is_missing_evidence_never_a_guess():
    norm = normalise_answers(SEC_QUESTIONS, {"years_sec": 6})
    j = {
        x.key: resolve(x, norm, None)[0]
        for x in FakeLLM().judge(JudgeRequest(SEC_SUPERVISOR_CRITERIA, Q, norm))
    }
    assert j["supervision"].missing_evidence and j["supervision"].level == 0
    assert not j["security_exp"].missing_evidence and j["security_exp"].level == 100


def test_evidence_mismatch_is_dropped():
    from app.llm.base import Judgement

    norm = normalise_answers(SEC_QUESTIONS, {"years_sec": 6})
    bad = Judgement("security_exp", 100, "form_field", "years_sec", "9")
    fixed, mismatch = verify_form_evidence(bad, norm)
    assert mismatch and fixed.missing_evidence and fixed.level == 0
