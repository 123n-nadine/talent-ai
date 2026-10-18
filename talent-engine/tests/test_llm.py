"""Local (vLLM) and cloud providers through a mocked OpenAI-compatible endpoint: guided JSON,
repair retry, quote verification, contradiction, and the settings switch between providers."""

from __future__ import annotations

import json

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.llm import registry
from app.llm.base import LLMOutputError
from app.llm.openai_compat import OpenAICompatLLM
from app.llm.schemas import CandidateProfile
from app.main import create_app
from app.pipeline.stages.profile import quote_in_text, verify_profile
from scripts.seed_data import JOBS
from tests.conftest import API_KEY, make_settings
from tests.test_documents import text_pdf_bytes

SEC = "HR-OPN-2026-0011"
CV_LINES = [
    "Shift supervisor at a large residential compound in Riyadh from 2019 to present",
    "I supervise 8 guards and prepare the weekly roster",
    "Security guard licence valid until 2027",
    "Arabic native, good English",
]
CV_TEXT = "\n".join(CV_LINES)

PROFILE_JSON = {
    "experience": [
        {
            "title": "Shift supervisor",
            "employer": None,
            "start": "2019",
            "end": "present",
            "team_size": 8,
            "quote": "Shift supervisor at a large residential compound in Riyadh from 2019 to present",
        },
        {
            "title": "Invented job",
            "start": "2010",
            "end": "2015",
            "team_size": 30,
            "quote": "this quote does not exist in the cv",
        },
    ],
    "certifications": [
        {
            "name": "Security guard licence",
            "status": "valid",
            "valid_until": "2027",
            "quote": "Security guard licence valid until 2027",
        }
    ],
    "skills": [],
    "languages": [{"language": "English", "level": "good", "quote": "Arabic native, good English"}],
    "education": [],
    "summary": "Shift supervisor since 2019.",
}


def judge_json(
    years_sup_form="4",
    cv_sup_level=75,
    quote="I supervise 8 guards and prepare the weekly roster",
    invented=False,
):
    rows = [
        {
            "key": "supervision",
            "form_level": 75,
            "form_field": "years_sup",
            "form_value": years_sup_form,
            "cv_level": cv_sup_level,
            "cv_quote": quote,
            "rationale": "أربع سنوات إشراف",
        },
        {
            "key": "security_exp",
            "form_level": 100,
            "form_field": "years_sec",
            "form_value": "6",
            "cv_level": None,
            "cv_quote": None,
            "rationale": "",
        },
        {
            "key": "shifts",
            "form_level": 100,
            "form_field": "shifts",
            "form_value": "أعددتها بنفسي",
            "cv_level": 100,
            "cv_quote": "prepare the weekly roster",
            "rationale": "",
        },
        {
            "key": "licence",
            "form_level": 100,
            "form_field": "licence",
            "form_value": "سارية",
            "cv_level": 100,
            "cv_quote": "licence valid until 2027"
            if not invented
            else "licence valid until 2099 forever",
            "rationale": "",
        },
        {
            "key": "reports",
            "form_level": 50,
            "form_field": "reports",
            "form_value": "أحيانًا",
            "cv_level": None,
            "cv_quote": None,
            "rationale": "",
        },
        {
            "key": "first_aid",
            "form_level": 0,
            "form_field": "first_aid",
            "form_value": "لا",
            "cv_level": None,
            "cv_quote": None,
            "rationale": "",
        },
        {
            "key": "languages",
            "form_level": 100,
            "form_field": "languages",
            "form_value": "العربية، الإنجليزية",
            "cv_level": 100,
            "cv_quote": "Arabic native, good English",
            "rationale": "",
        },
    ]
    return {"criteria": rows}


class MockLLM:
    """Pretends to be vLLM / a cloud API. Records requests; answers by task."""

    def __init__(self, judge=None, profile=None, broken_first=False, cut_first=False):
        self.requests: list[dict] = []
        self.judge = judge or judge_json()
        self.profile = profile or PROFILE_JSON
        self.broken_first = broken_first
        self.cut_first = cut_first  # the first answer stops at the output budget, JSON unclosed
        self.calls = 0

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        if request.url.path.endswith("/models"):
            return httpx2.Response(
                200, json={"object": "list", "data": [{"id": "qwen3-8b-awq", "object": "model"}]}
            )
        body = json.loads(request.content)
        self.requests.append(
            {"headers": dict(request.headers), "body": body, "url": str(request.url)}
        )
        self.calls += 1
        name = body["response_format"]["json_schema"]["name"]
        finish = "stop"
        if self.broken_first and self.calls == 1:
            content = "{not json"
        elif self.cut_first and self.calls == 1:
            content = json.dumps(self.profile, ensure_ascii=False)[:120]  # cut mid-way, like vLLM
            finish = "length"
        elif name == "candidate_profile":
            content = json.dumps(self.profile, ensure_ascii=False)
        elif name == "judgement":
            content = json.dumps(self.judge, ensure_ascii=False)
        else:
            content = json.dumps({"description": "d", "criteria": [], "questions": []})
        return httpx2.Response(
            200,
            json={
                "id": "x",
                "object": "chat.completion",
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish,
                    }
                ],
                "usage": {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1500},
            },
        )

    def client(self) -> httpx2.Client:
        return httpx2.Client(transport=httpx2.MockTransport(self.handler))


@pytest.fixture
def mock_llm(monkeypatch):
    m = MockLLM()
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    yield m
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", None)


def _client(tmp_path, **overrides):
    settings = make_settings(file_store=str(tmp_path / "files"), **overrides)
    c = TestClient(create_app(settings))
    c.__enter__()
    c.headers.update({"Authorization": f"Bearer {API_KEY}", "X-Talent-Actor": "pytest"})
    return c


def _seed(c, with_cv=True):
    c.put(f"/v1/jobs/{SEC}", json=JOBS[SEC])
    c.put(
        "/v1/candidates/C-LLM",
        json={
            "facts": {"nationality": "السعودية", "height_cm": 181, "weight_kg": 79, "age": 29},
            "answers": {
                "years_sup": 4,
                "years_sec": 6,
                "shifts": "أعددتها بنفسي",
                "licence": "سارية",
                "reports": "أحيانًا",
                "first_aid": "لا",
                "languages": ["العربية", "الإنجليزية"],
            },
        },
    )
    if with_cv:
        r = c.put(
            "/v1/candidates/C-LLM/cv",
            files={"file": ("cv.pdf", text_pdf_bytes(CV_LINES), "application/pdf")},
        )
        assert r.json()["document"]["status"] == "ready"
    r = c.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "C-LLM"})
    return c.get(f"/v1/screenings/{r.json()['screening_id']}").json()


def test_local_provider_full_cycle(tmp_path, mock_llm):
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c)
    assert s["status"] == "completed", s["error"]
    assert s["versions"]["provider"] == "local" and s["versions"]["model"] == "qwen3-8b-awq"
    assert s["versions"]["prompt"] == "judge-v1" and len(s["versions"]["llm_calls"]) == 2
    assert s["score"] == 81.5  # same levels as the worked example
    by = {x["key"]: x for x in s["criteria"]}
    assert (
        by["supervision"]["confirmed_by_cv"] is True and by["supervision"]["source"] == "form_field"
    )
    assert (
        by["licence"]["confirmed_by_cv"] is True and by["security_exp"]["confirmed_by_cv"] is False
    )
    assert by["supervision"]["cv_quote"] == "I supervise 8 guards and prepare the weekly roster"
    assert by["supervision"]["form_level"] == 75 and by["supervision"]["cv_level"] == 75
    assert by["security_exp"]["cv_quote"] is None
    stages = {st["key"]: st for st in s["stages"]}
    assert stages["profile"]["status"] == "done" and stages["evidence_check"]["status"] == "done"
    assert (
        "عنصر واحد بلا اقتباس (حُذف)" in stages["evidence_check"]["note"]
    )  # the invented item was dropped
    # the request to the model: thinking off, json schema, temperature 0, no facts/name in the prompt
    judge_req = [
        r
        for r in mock_llm.requests
        if r["body"]["response_format"]["json_schema"]["name"] == "judgement"
    ][0]
    assert judge_req["body"]["temperature"] == 0 and judge_req["body"]["chat_template_kwargs"] == {
        "enable_thinking": False
    }
    prompt = json.dumps(judge_req["body"]["messages"], ensure_ascii=False)
    assert "السعودية" not in prompt and "181" not in prompt and "supervision_years" in prompt
    c.__exit__(None, None, None)


def test_contradiction_uses_lower_level_and_needs_review(tmp_path, monkeypatch):
    m = MockLLM(judge=judge_json(cv_sup_level=50))  # CV supports only 50 while the answer says 75
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c)
    sup = next(x for x in s["criteria"] if x["key"] == "supervision")
    assert (
        sup["contradiction"] is True
        and sup["effective_level"] == 50
        and sup["source"] == "cv_quote"
    )
    assert "إجابة النموذج: 4" in sup["evidence"]
    assert s["ai_status"] == "Needs Review" and "contradiction" in s["flags"] and s["score"] == 74.0
    c.__exit__(None, None, None)


def test_invented_quote_is_dropped_never_guessed(tmp_path, monkeypatch):
    m = MockLLM(judge=judge_json(invented=True))
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c)
    lic = next(x for x in s["criteria"] if x["key"] == "licence")
    assert (
        lic["confirmed_by_cv"] is False and lic["source"] == "form_field"
    )  # form evidence still valid
    assert "quote_not_found" in s["flags"]
    c.__exit__(None, None, None)


def test_structured_answers_are_judged_in_code_not_by_the_model(tmp_path, monkeypatch):
    m = MockLLM(judge=judge_json(years_sup_form="9"))  # the model misquotes the stored answer
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c, with_cv=False)
    # every criterion of this profile is fed by a structured question: no model call is needed at all
    assert m.requests == [] and s["status"] == "completed" and s["score"] == 81.5
    sup = next(x for x in s["criteria"] if x["key"] == "supervision")
    assert sup["effective_level"] == 75 and sup["evidence"] == "4" and sup["source"] == "form_field"
    assert "بدون نموذج لغوي" in next(st for st in s["stages"] if st["key"] == "judgement")["note"]
    c.__exit__(None, None, None)


def test_invalid_json_repaired_once_then_fails(monkeypatch):
    m = MockLLM(broken_first=True)
    p = OpenAICompatLLM(
        "local", "http://vllm:8000/v1", "EMPTY", "qwen3-8b-awq", http_client=m.client()
    )
    prof = p.profile(CV_TEXT)
    assert isinstance(prof, CandidateProfile) and m.calls == 2  # one repair round trip
    assert "corrected JSON" in m.requests[1]["body"]["messages"][1]["content"]

    class AlwaysBroken(MockLLM):
        def handler(self, request):
            self.calls += 1
            return httpx2.Response(
                200,
                json={
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "nope"}}]
                },
            )

    b = AlwaysBroken()
    p2 = OpenAICompatLLM(
        "local", "http://vllm:8000/v1", "EMPTY", "qwen3-8b-awq", http_client=b.client()
    )
    with pytest.raises(LLMOutputError):
        p2.profile(CV_TEXT)
    assert b.calls == 2


def test_cloud_switch_is_only_a_setting(tmp_path, monkeypatch):
    seen = {}

    class CloudMock(MockLLM):
        def handler(self, request):
            seen["auth"] = request.headers.get("authorization")
            seen["host"] = request.url.host
            return super().handler(request)

    m = CloudMock()
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(
        tmp_path,
        ai_provider="fake",
        cloud_llm_api_key="sk-test-dummy",
        cloud_llm_base_url="https://cloud.example/v1",
        cloud_llm_model="cloud-model-x",
    )
    r = c.put("/v1/settings", json={"ai_provider": "cloud"})
    assert (
        r.status_code == 200
        and r.json()["ai_provider"] == "cloud"
        and r.json()["ai_model"] == "cloud-model-x"
    )
    s = _seed(c)
    assert (
        s["status"] == "completed"
        and s["versions"]["provider"] == "cloud"
        and s["versions"]["model"] == "cloud-model-x"
    )
    assert seen["auth"] == "Bearer sk-test-dummy" and seen["host"] == "cloud.example"
    cloud_req = [
        r for r in m.requests if r["body"]["response_format"]["json_schema"]["name"] == "judgement"
    ][0]
    assert (
        "chat_template_kwargs" not in cloud_req["body"]
    )  # vLLM-only knob is not sent to a cloud API
    # and without a key the switch is refused
    c2 = _client(tmp_path / "b", ai_provider="fake", cloud_llm_api_key="")
    assert c2.put("/v1/settings", json={"ai_provider": "cloud"}).status_code == 422
    c.__exit__(None, None, None)
    c2.__exit__(None, None, None)


def test_quote_matching_and_years_in_code():
    assert quote_in_text("Shift supervisor at a large", CV_TEXT)
    assert quote_in_text(
        "shift supervisor at a larg residential", CV_TEXT
    )  # one typo, fuzzy >= 0.9
    assert not quote_in_text("no such text anywhere", CV_TEXT) and not quote_in_text(
        "short", CV_TEXT
    )
    from datetime import UTC, datetime

    prof = CandidateProfile.model_validate(PROFILE_JSON)
    vp = verify_profile(prof, CV_TEXT, now=datetime(2026, 10, 15, tzinfo=UTC))
    assert vp.dropped == 1 and len(vp.data["experience"]) == 1
    assert vp.derived["supervision_years"] == 7.8 and vp.derived["max_team_size"] == 8
    assert vp.derived["valid_certifications"] == ["Security guard licence"]


def test_strict_schema_requires_every_property():
    from app.llm.openai_compat import strict_schema

    sch = strict_schema(CandidateProfile)
    assert (
        set(sch["required"]) == set(sch["properties"].keys())
        and sch["additionalProperties"] is False
    )
    exp = sch["$defs"]["ExperienceItem"]
    assert "team_size" in exp["required"] and exp["additionalProperties"] is False


def test_form_value_tolerance_and_question_from_job():
    from app.llm.schemas import CriterionJudgement
    from app.llm.templates import SEC_QUESTIONS
    from app.pipeline.stages.answers import normalise_answers
    from app.pipeline.stages.evidence import resolve

    norm = normalise_answers(SEC_QUESTIONS, {"years_sup": 7})
    raw = CriterionJudgement(
        key="supervision", form_level=100, form_field=None, form_value="7 سنوات"
    )
    j, probs = resolve(raw, norm, None, question_key="years_sup")
    assert j.level == 100 and j.source == "form_field" and j.evidence == "7" and probs == []
    raw2 = CriterionJudgement(key="supervision", form_level=100, form_field=None, form_value="9")
    j2, probs2 = resolve(raw2, norm, None, question_key="years_sup")
    assert j2.missing_evidence and probs2 == ["evidence_mismatch"]


def test_llm_draft_is_normalised_into_an_approvable_job():
    from app.domain.models import JobIn
    from app.llm.draft import normalise_draft
    from app.llm.schemas import DraftOutput

    raw = DraftOutput.model_validate(
        {
            "description": "وصف",
            "criteria": [
                {
                    "key": "خبرة في المحاسبة",
                    "text": "خبرة في المحاسبة",
                    "weight": 30,
                    "mandatory": True,
                    "question": "ما عدد سنوات خبرتك في مجال المحاسبة؟",
                    "rubric": [{"level": 0, "text": "لا"}, {"level": 100, "text": "أكثر من 5"}],
                },
                {
                    "key": "tax_law",
                    "text": "القوانين الضريبية",
                    "weight": 50,
                    "question": "tax_q",
                    "rubric": [{"level": lv, "text": str(lv)} for lv in (0, 25, 50, 75, 100)],
                },
                {
                    "key": "teamwork",
                    "text": "العمل ضمن فريق",
                    "weight": 20,
                    "question": "سؤال غير موجود إطلاقًا",
                    "rubric": [{"level": lv, "text": str(lv)} for lv in (0, 25, 50, 75, 100)],
                },
            ],
            "questions": [
                {
                    "key": "سنوات الخبرة",
                    "label": "ما عدد سنوات خبرتك في مجال المحاسبة؟",
                    "type": "number",
                },
                {
                    "key": "tax_q",
                    "label": "ما مستوى معرفتك بالقوانين الضريبية؟",
                    "type": "select",
                    "options": [],
                },
            ],
        }
    )
    d = normalise_draft(raw)
    assert [c["key"] for c in d.criteria] == ["c1", "tax_law", "teamwork"]
    assert [q["key"] for q in d.questions] == ["q1", "tax_q"]
    assert [c["question"] for c in d.criteria] == ["q1", "tax_q", None]
    assert d.questions[1]["type"] == "text"  # a select without options becomes free text
    assert [r["level"] for r in d.criteria[0]["rubric"]] == [0, 25, 50, 75, 100]
    assert sum(c["weight"] for c in d.criteria) == 100
    JobIn.model_validate(
        {
            "title": "محاسب",
            "description": d.description,
            "criteria": d.criteria,
            "questions": d.questions,
            "rules": [],
        }
    )  # approvable as is


def test_cv_duration_is_levelled_in_code_not_by_the_model():
    """Demo 2012: the model gave «لمدة سنتين» level 100; code reads 2 years -> 50 -> contradiction."""
    from app.llm.schemas import CriterionJudgement
    from app.llm.templates import SEC_QUESTIONS, YEARS_RUBRIC
    from app.pipeline.stages.answers import normalise_answers
    from app.pipeline.stages.evidence import resolve
    from app.scoring.rubric import years_in_quote

    assert years_in_quote("أشرفت على فريق صغير من الحراس لمدة سنتين") == 2
    assert years_in_quote("خبرة أمنية7. سنوات") == 7  # digit moved by PDF bidi extraction
    assert years_in_quote("ثلاث سنوات في الإشراف") == 3
    assert years_in_quote("Total experience in security: 10 years.") == 10
    assert years_in_quote("أشرف على 14 فرد أمن") is None
    text = "حارس أمن في مجمع تجاري.\nأشرفت على فريق صغير من الحراس لمدة سنتين.\n"
    norm = normalise_answers(SEC_QUESTIONS, {"years_sup": 6})
    raw = CriterionJudgement(
        key="supervision",
        form_level=100,
        form_value="6",
        cv_level=100,
        cv_quote="أشرفت على فريق صغير من الحراس لمدة سنتين",
    )
    j, probs = resolve(
        raw, norm, text, question_key="years_sup", code_level=100, numeric_rubric=YEARS_RUBRIC
    )
    assert probs == []
    assert j.cv_level == 50 and j.form_level == 100
    assert j.contradiction and j.level == 50


def gold_cv_text(ref: str) -> str:
    """The CV of a gold-set applicant as the redacted text the model sees."""
    gold = json.load(
        open("eval/gold/security_supervisor.json", encoding="utf-8")
    )  # synthetic, committed
    app = next(a for a in gold["applicants"] if a["ref"] == ref)
    return "\n".join(app["cv_lines"])


def test_cut_off_profile_is_retried_shorter_not_repaired():
    """Round 7: GOLD-SEC-015's profile answer hit the output budget three times (unclosed JSON).
    The answer budget is now what the context leaves, and a cut-off answer is retried once with a
    trimmed CV and a request for a compact answer instead of the same request again."""
    m = MockLLM(cut_first=True)
    p = OpenAICompatLLM(
        "local", "http://vllm:8000/v1", "EMPTY", "qwen3-8b-awq", http_client=m.client()
    )
    prof = p.profile(gold_cv_text("GOLD-SEC-015"))
    assert isinstance(prof, CandidateProfile) and m.calls == 2
    first, second = (r["body"] for r in m.requests)
    assert first["max_tokens"] == 2500  # the cap, inside the 8192 context
    lists = first["response_format"]["json_schema"]["schema"]
    assert all(
        v.get("maxItems") == 12 for v in lists["properties"].values() if v.get("type") == "array"
    )  # a repeating model is stopped by the grammar
    assert (
        first["max_tokens"]
        + len(first["messages"][0]["content"] + first["messages"][1]["content"]) // 2
        <= 8192
    )
    cut = second["messages"][1]["content"]
    assert "cut off" in cut and "compact" in cut and "corrected JSON" not in cut  # not a repair
    assert "GOLD" not in cut  # the retry still carries only the CV text and the note
    assert p.last_usage["retried_shorter"] is True and p.last_usage["finish_reason"] == "stop"


def test_output_budget_follows_the_context():
    p = OpenAICompatLLM("local", "http://vllm:8000/v1", "EMPTY", "m", max_model_len=8192)
    assert p.output_budget("candidate_profile", "x" * 200, "y" * 600) == 2500  # the cap
    assert p.output_budget("candidate_profile", "x" * 200, "y" * 15000) == 8192 - 7800 - 64
    assert (
        p.output_budget("candidate_profile", "x" * 200, "y" * 40000) == 256
    )  # never below the floor


def test_long_cv_is_cut_at_a_line_for_the_retry():
    from app.llm.openai_compat import shorten

    text = "\n".join(f"سطر رقم {i} في السيرة الذاتية" for i in range(100))
    short = shorten(text, 500)
    assert len(short) <= 500 and short.endswith("الذاتية") and short.count("\n") < text.count("\n")
    assert shorten("قصير", 500) == "قصير"


def test_partial_cv_read_is_flagged_for_hr(tmp_path, monkeypatch):
    """Round 8: when the profile answer overran the budget and the retry read a trimmed CV, the
    screening carries «cv_partial_read» so the Frappe card and the console say the CV evidence
    covers the first part of the text only."""
    m = MockLLM(cut_first=True)
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c)
    assert s["status"] == "completed" and "cv_partial_read" in s["flags"]
    prof = next(x for x in s["versions"]["llm_calls"] if x["task"] == "profile")
    assert prof["retried_shorter"] is True
    c.__exit__(None, None, None)


def test_repeated_profile_items_are_kept_once():
    """Round 8: an 8B model may write one language or certification item many times; the code
    keeps the first occurrence and counts the rest, before anything is shown or saved."""
    text = "\n".join(CV_LINES)
    lang = {"language": "العربية", "level": "لغة أم", "quote": CV_LINES[-1]}
    cert = {"name": "رخصة حارس أمن", "status": "valid", "quote": CV_LINES[3]}
    prof = CandidateProfile(
        languages=[lang] * 12,
        certifications=[cert, {**cert, "quote": CV_LINES[3] + " "}, {**cert, "status": "expired"}],
        experience=[],
    )
    vp = verify_profile(prof, text)
    assert len(vp.data["languages"]) == 1 and vp.data["languages"][0]["language"] == "العربية"
    assert [c["status"] for c in vp.data["certifications"]] == ["valid", "expired"]
    assert vp.duplicates == 12 and vp.dropped == 0
