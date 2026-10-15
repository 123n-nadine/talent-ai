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

    def __init__(self, judge=None, profile=None, broken_first=False):
        self.requests: list[dict] = []
        self.judge = judge or judge_json()
        self.profile = profile or PROFILE_JSON
        self.broken_first = broken_first
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
        if self.broken_first and self.calls == 1:
            content = "{not json"
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
                        "finish_reason": "stop",
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
    stages = {st["key"]: st for st in s["stages"]}
    assert stages["profile"]["status"] == "done" and stages["evidence_check"]["status"] == "done"
    assert "1 حُذف" in stages["evidence_check"]["note"]  # the invented experience item was dropped
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


def test_form_value_mismatch_becomes_missing_evidence(tmp_path, monkeypatch):
    m = MockLLM(judge=judge_json(years_sup_form="9"))  # the model misquoted the stored answer
    monkeypatch.setattr(registry, "HTTP_CLIENT_FACTORY", lambda name: m.client())
    c = _client(tmp_path, ai_provider="local")
    s = _seed(c, with_cv=False)
    sup = next(x for x in s["criteria"] if x["key"] == "supervision")
    assert (
        sup["missing_evidence"] is True
        and sup["effective_level"] == 0
        and "evidence_mismatch" in s["flags"]
    )
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
