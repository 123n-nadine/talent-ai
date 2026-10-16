from __future__ import annotations

import copy

import httpx

from app.core.security import verify_callback
from scripts.seed_data import JOBS

SEC = "HR-OPN-2026-0011"


def test_auth_required(client):
    r = client.get("/v1/jobs", headers={"Authorization": ""})
    assert r.status_code == 401
    r = client.get("/v1/jobs", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json()["ready"] is True


def test_weights_must_total_100(client, sec_job):
    bad = copy.deepcopy(sec_job)
    bad["criteria"][2]["weight"] = 20  # total 105
    r = client.put(f"/v1/jobs/{SEC}", json=bad)
    assert r.status_code == 422
    assert "100%" in r.text
    ok = client.put(f"/v1/jobs/{SEC}", json=sec_job)
    assert ok.status_code == 200 and ok.json()["version"]["weights_total"] == 100


def test_same_content_does_not_create_new_version(client, sec_job):
    a = client.put(f"/v1/jobs/{SEC}", json=sec_job).json()
    b = client.put(f"/v1/jobs/{SEC}", json=sec_job).json()
    assert a["new_version"] is True and b["new_version"] is False
    assert b["version"]["version"] == 1


def test_unknown_fact_rejected(client):
    r = client.put("/v1/candidates/X-1", json={"facts": {"name": "x"}, "answers": {}})
    assert r.status_code == 422 and "name" in r.json()["detail"]["unknown_facts"]


def test_full_cycle_matches_the_demo(client, seeded):
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    order = [(it["candidate_ref"], it["score"]) for it in rk["ranked"]]
    assert order == [
        ("HR-APP-2026-2001", 100.0),
        ("HR-APP-2026-2012", 90.5),
        ("HR-APP-2026-2003", 89.0),
        ("HR-APP-2026-2002", 81.5),
        ("HR-APP-2026-2014", 80.0),
        ("HR-APP-2026-2017", 78.0),
        ("HR-APP-2026-2013", 65.0),
        ("HR-APP-2026-2004", 63.0),
        ("HR-APP-2026-2005", 48.5),
        ("HR-APP-2026-2015", 47.5),
        ("HR-APP-2026-2006", 5.0),
        ("HR-APP-2026-2007", 5.0),
    ]
    groups = {g: [x["candidate_ref"] for x in items] for g, items in rk["groups"].items()}
    assert groups["not_eligible"] == ["HR-APP-2026-2010", "HR-APP-2026-2011"]
    assert groups["needs_review"] == ["HR-APP-2026-2008", "HR-APP-2026-2009"]
    assert groups["duplicate"] == ["HR-APP-2026-2016"]
    assert groups["processing"] == [] and groups["failed"] == [] and groups["stale"] == []
    assert rk["ranked_total"] == 12 and rk["total"] == 17


def test_worked_example_details(client, seeded):
    s = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2002']}").json()
    assert s["score"] == 81.5 and s["coverage"] == 1.0 and s["band"] == "high"
    assert s["ai_status"] == "Completed" and s["eligibility"] == "eligible"
    assert s["rank"] == 4 and s["ranked_total"] == 12
    by_key = {c["key"]: c for c in s["criteria"]}
    assert by_key["supervision"]["level"] == 75 and by_key["supervision"]["evidence"] == "4"
    assert by_key["first_aid"]["level"] == 0 and by_key["first_aid"]["evidence"] == "لا"
    assert all(c["source"] == "form_field" for c in s["criteria"])
    assert (
        s["raise_score"][0]["criterion"] == "supervision" and s["raise_score"][0]["points"] == 7.5
    )
    assert "الدرجة ترتيب" in s["disclaimer"]
    skipped = [st for st in s["stages"] if st["status"] == "skipped"]
    assert any("لا توجد سيرة" in (st["note"] or "") for st in skipped)


def test_blank_vs_zero_and_needs_review(client, seeded):
    s5 = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2005']}").json()
    lang = next(c for c in s5["criteria"] if c["key"] == "languages")
    assert lang["missing_evidence"] is True and lang["effective_level"] == 0
    assert s5["coverage"] == 0.95 and s5["ai_status"] == "Completed" and s5["band"] == "low"
    s6 = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2006']}").json()
    sup = next(c for c in s6["criteria"] if c["key"] == "supervision")
    assert sup["missing_evidence"] is False and sup["evidence"] == "0" and sup["level"] == 0
    assert "mandatory_zero" in s6["flags"] and s6["band"] == "low"
    s9 = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2009']}").json()
    assert (
        s9["coverage"] == 0.25
        and s9["ai_status"] == "Needs Review"
        and "low_coverage" in s9["flags"]
    )
    assert "mandatory_missing" in s9["flags"]


def test_not_eligible_is_kept_not_rejected(client, seeded):
    s = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2010']}").json()
    assert s["eligibility"] == "not_eligible" and s["status"] == "completed" and s["rank"] is None
    assert s["eligibility_reasons"] == ["الطول (سم): المصرّح به 172 سم — المطلوب 180 سم أو أكثر"]
    assert s["score"] == 96.0  # computed and shown, just not ranked
    s8 = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2008']}").json()
    assert s8["eligibility"] == "needs_review" and s8["ai_status"] == "Needs Review"


def test_duplicate_linked_nothing_deleted(client, seeded):
    s = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2016']}").json()
    assert (
        s["duplicate_of"] == "HR-APP-2026-2015" and "duplicate" in s["flags"] and s["rank"] is None
    )
    assert client.get("/v1/candidates/HR-APP-2026-2016").status_code == 200
    orig = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2015']}").json()
    assert orig["rank"] is not None


def test_override_requires_reason_and_recomputes(client, seeded):
    sid = seeded["HR-APP-2026-2002"]
    r = client.post(
        f"/v1/screenings/{sid}/override",
        json={"criterion_key": "first_aid", "level": 100, "reason": "", "by": "hr"},
    )
    assert r.status_code == 422
    r = client.post(
        f"/v1/screenings/{sid}/override",
        json={
            "criterion_key": "first_aid",
            "level": 100,
            "reason": "قدّم شهادة إسعافات حديثة في المقابلة",
            "by": "hr.user",
        },
    )
    assert r.status_code == 200
    s = r.json()
    assert s["score"] == 88.5 and "hr_override" in s["flags"]
    fa = next(c for c in s["criteria"] if c["key"] == "first_aid")
    assert fa["overridden_level"] == 100 and fa["override_by"] == "hr.user" and fa["level"] == 0
    ev = client.get(
        "/v1/audit", params={"ref": "HR-APP-2026-2002", "action": "screening.override"}
    ).json()["events"]
    assert ev and ev[0]["actor"] == "hr.user" and ev[0]["payload"]["reason"]


def test_edit_after_evaluation_marks_stale_until_rescreen(client, seeded):
    sid = seeded["HR-APP-2026-2001"]
    cand = client.get("/v1/candidates/HR-APP-2026-2001").json()
    answers = dict(cand["answers"])
    answers["years_sup"] = 1
    client.put(
        "/v1/candidates/HR-APP-2026-2001",
        json={"id_token": cand["id_token"], "facts": cand["facts"], "answers": answers},
    )
    s = client.get(f"/v1/screenings/{sid}").json()
    assert s["current"] is False and s["stale_reason"] == "data_changed" and s["rank"] is None
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert [x["candidate_ref"] for x in rk["groups"]["stale"]] == ["HR-APP-2026-2001"]
    assert rk["ranked"][0]["candidate_ref"] == "HR-APP-2026-2012"
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2001"})
    assert r.status_code == 202 and r.json()["created"] is True
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    me = next(x for x in rk["ranked"] if x["candidate_ref"] == "HR-APP-2026-2001")
    assert me["score"] == 85.0 and rk["groups"]["stale"] == []


def test_new_profile_version_makes_results_stale_and_rescreen_updates(client, seeded, sec_job):
    changed = copy.deepcopy(sec_job)
    changed["criteria"][2]["weight"] = 20
    changed["criteria"][3]["weight"] = 10
    r = client.put(f"/v1/jobs/{SEC}", json=changed)
    assert r.json()["version"]["version"] == 2
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert (
        rk["ranked"] == [] and len(rk["groups"]["stale"]) == 17 - 1
    )  # the duplicate stays in its group
    r = client.post(f"/v1/jobs/{SEC}/rescreen")
    assert r.status_code == 202 and len(r.json()["queued"]) == 17
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert rk["job_version"] == 2 and rk["ranked_total"] == 12
    s2 = next(x for x in rk["ranked"] if x["candidate_ref"] == "HR-APP-2026-2002")
    assert (
        s2["score"] == 81.5
    )  # shifts 100 and licence 100: moving 5 points between them changes nothing
    s3 = next(x for x in rk["ranked"] if x["candidate_ref"] == "HR-APP-2026-2003")
    assert s3["score"] == 86.5  # shifts 50 (20 -> 10 pts) vs licence 100 (15 -> 10 pts)


def test_idempotent_screening_by_input_hash(client, seeded):
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2002"})
    assert (
        r.status_code == 202
        and r.json()["created"] is False
        and r.json()["screening_id"] == seeded["HR-APP-2026-2002"]
    )
    r = client.post(
        "/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2002", "force": True}
    )
    assert r.json()["created"] is True


def test_delete_candidate_removes_everything(client, seeded):
    r = client.delete("/v1/candidates/HR-APP-2026-2002")
    assert r.status_code == 200 and r.json()["removed"]["screenings"] == 1
    assert client.get("/v1/candidates/HR-APP-2026-2002").status_code == 404
    assert client.get(f"/v1/screenings/{seeded['HR-APP-2026-2002']}").status_code == 404
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert (
        all(x["candidate_ref"] != "HR-APP-2026-2002" for x in rk["ranked"])
        and rk["ranked_total"] == 11
    )


def test_two_jobs_do_not_mix(client, seeded):
    client.put("/v1/jobs/HR-OPN-2026-0013", json=JOBS["HR-OPN-2026-0013"])
    client.put(
        "/v1/candidates/HR-APP-2026-1951",
        json={
            "facts": {"nationality": "السعودية", "age": 27},
            "answers": {"sql": "متقدم", "python": "جيد", "dashboards": "متقدم"},
        },
    )
    client.post(
        "/v1/screenings", json={"job_ref": "HR-OPN-2026-0013", "candidate_ref": "HR-APP-2026-1951"}
    )
    a = client.get("/v1/jobs/HR-OPN-2026-0013/ranking").json()
    assert [x["candidate_ref"] for x in a["ranked"]] == ["HR-APP-2026-1951"] and a["ranked"][0][
        "score"
    ] == 92.5
    b = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert all(x["candidate_ref"] != "HR-APP-2026-1951" for x in b["ranked"])


def test_settings_engine_owned(client):
    s = client.get("/v1/settings").json()
    assert s["ai_provider"] == "fake" and s["provider_ready"] is True
    r = client.put("/v1/settings", json={"ai_provider": "cloud"})
    assert r.status_code == 422 and "CLOUD_LLM_API_KEY" in r.text
    r = client.put("/v1/settings", json={"ai_provider": "local"})
    assert r.status_code == 422
    r = client.put(
        "/v1/settings",
        json={
            "max_retries": 5,
            "allowed_facts": ["nationality", "age", "height_cm", "weight_kg", "gender"],
        },
    )
    assert (
        r.status_code == 200
        and r.json()["max_retries"] == 5
        and "gender" in r.json()["allowed_facts"]
    )
    ev = client.get("/v1/audit", params={"action": "settings.updated"}).json()["events"]
    assert ev and ev[0]["payload"]["max_retries"] == 5


def test_draft_criteria_sums_to_100(client):
    r = client.post("/v1/jobs/draft-criteria", json={"title": "مشرف أمن"})
    assert r.status_code == 200 and r.json()["draft"] is True and r.json()["weights_total"] == 100
    r = client.post("/v1/jobs/draft-criteria", json={"title": "محاسب"})
    assert r.json()["weights_total"] == 100


def test_callback_is_signed_and_delivered(monkeypatch, sec_job):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.services import callback as cb
    from tests.conftest import API_KEY, make_settings

    received = []

    def handler(request: httpx.Request) -> httpx.Response:
        ok = verify_callback(
            "cb-secret",
            request.headers["X-Talent-Timestamp"],
            request.content,
            request.headers["X-Talent-Signature"],
        )
        received.append((ok, request.headers["X-Talent-Event"]))
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    original = cb.send

    def patched(url, secret, payload, settings, event="screening.result", client=None):
        return original(
            url, secret, payload, settings, event, client=httpx.Client(transport=transport)
        )

    monkeypatch.setattr("app.pipeline.runner.send_callback", patched)
    settings = make_settings(
        callback_url="http://frappe.local/api/method/ido_talent_ai.api.receive_result",
        callback_secret="cb-secret",
    )
    with TestClient(create_app(settings)) as client:
        client.headers.update({"Authorization": f"Bearer {API_KEY}"})
        client.put(f"/v1/jobs/{SEC}", json=sec_job)
        client.put(
            "/v1/candidates/C-1",
            json={
                "facts": {"nationality": "السعودية", "height_cm": 181, "weight_kg": 79, "age": 29},
                "answers": {"years_sup": 4, "years_sec": 6},
            },
        )
        client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "C-1"})
        ev = client.get("/v1/audit", params={"ref": "C-1", "action": "callback.sent"}).json()[
            "events"
        ]
    assert received == [(True, "screening.result")]
    assert ev and ev[0]["payload"]["ok"] is True


def test_engine_failure_becomes_failed_after_retries_then_retry_works(monkeypatch, client, sec_job):
    from app.llm import fake as fake_mod

    calls = {"n": 0}
    real_judge = fake_mod.FakeLLM.judge

    def boom(self, req):
        calls["n"] += 1
        raise RuntimeError("LLM down")

    monkeypatch.setattr(fake_mod.FakeLLM, "judge", boom)
    monkeypatch.setattr(
        "app.pipeline.runner.is_code_judged", lambda c, q: False
    )  # force the model path
    client.put(f"/v1/jobs/{SEC}", json=sec_job)
    client.put(
        "/v1/candidates/C-9",
        json={
            "facts": {"nationality": "السعودية", "height_cm": 181, "weight_kg": 79, "age": 29},
            "answers": {"years_sup": 4},
        },
    )
    sid = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "C-9"}).json()[
        "screening_id"
    ]
    s = client.get(f"/v1/screenings/{sid}").json()
    assert (
        s["status"] == "failed"
        and s["ai_status"] == "Failed"
        and s["attempts"] == 3
        and "LLM down" in s["error"]
    )
    assert calls["n"] == 3
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert [x["candidate_ref"] for x in rk["groups"]["failed"]] == ["C-9"]
    monkeypatch.setattr(fake_mod.FakeLLM, "judge", real_judge)
    r = client.post(f"/v1/screenings/{sid}/retry")
    assert r.status_code == 202
    s = client.get(f"/v1/screenings/{sid}").json()
    assert s["status"] in ("completed", "needs_review") and s["error"] is None


def test_unknown_rule_operator_rejected_by_api(client, sec_job):
    bad = copy.deepcopy(sec_job)
    bad["rules"][1]["operator"] = "~="
    r = client.put(f"/v1/jobs/{SEC}", json=bad)
    assert r.status_code == 422


def test_api_key_rotation_on_restart():
    from sqlalchemy import select

    from app.core.security import hash_api_key
    from app.main import ensure_default_tenant
    from app.storage.db import make_engine, make_sessionmaker
    from app.storage.models import Base, Tenant
    from tests.conftest import make_settings

    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sm = make_sessionmaker(engine)
    ensure_default_tenant(sm, make_settings(tenant_api_key="old-key"))
    ensure_default_tenant(sm, make_settings(tenant_api_key="new-key"))
    with sm() as db:
        tenants = db.scalars(select(Tenant)).all()
        assert len(tenants) == 1
        assert tenants[0].api_key_hash == hash_api_key("new-key")


def test_impact_preview_keeps_levels_and_moves_weights(client, seeded, sec_job):
    crit = copy.deepcopy(sec_job["criteria"])
    crit[2]["weight"] = 20  # shifts 15 -> 20
    crit[3]["weight"] = 10  # licence 15 -> 10
    r = client.post(f"/v1/jobs/{SEC}/impact", json={"criteria": crit})
    assert r.status_code == 200, r.text
    d = r.json()
    by = {x["candidate_ref"]: x for x in d["rows"]}
    assert (
        by["HR-APP-2026-2002"]["old_score"] == 81.5 and by["HR-APP-2026-2002"]["new_score"] == 81.5
    )
    assert (
        by["HR-APP-2026-2003"]["old_score"] == 89.0 and by["HR-APP-2026-2003"]["new_score"] == 86.5
    )
    assert (
        by["HR-APP-2026-2010"]["rankable"] is False and by["HR-APP-2026-2010"]["new_rank"] is None
    )
    assert d["weights_total"] == 100 and d["summary"]["score_changed"] >= 1
    # nothing was written: the ranking is unchanged
    assert client.get(f"/v1/jobs/{SEC}/ranking").json()["ranked"][2]["score"] == 89.0


def test_delete_job_removes_versions_and_screenings_but_keeps_candidates(client, seeded):
    r = client.delete("/v1/jobs/HR-OPN-2026-0011")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["screenings"] >= 17 and body["versions"] == 1
    assert client.get("/v1/jobs/HR-OPN-2026-0011").status_code == 404
    assert client.get("/v1/candidates/HR-APP-2026-2001").status_code == 200
    assert client.delete("/v1/jobs/HR-OPN-2026-0011").status_code == 404


def test_applied_at_orders_duplicates_and_starts_retention(client, sec_job):
    client.put("/v1/jobs/HR-OPN-2026-0011", json=sec_job)
    base = {"id_token": "tok-same-person", "facts": {"nationality": "السعودية", "height_cm": 181, "weight_kg": 78, "age": 30},
            "answers": {"years_sup": 3}, "retention_days": 30}
    # the engine sees the later application first (e.g. after a retry on the host)
    r = client.put("/v1/candidates/LATE", json={**base, "applied_at": "2026-10-10T10:00:00Z"})
    assert r.status_code == 200, r.text
    client.put("/v1/candidates/EARLY", json={**base, "applied_at": "2026-10-01T10:00:00+03:00"})
    early = client.get("/v1/candidates/EARLY").json()
    assert early["applied_at"].startswith("2026-10-01T07:00:00")
    assert early["retention_until"].startswith("2026-10-31T07:00:00")
    s1 = client.post("/v1/screenings", json={"job_ref": "HR-OPN-2026-0011", "candidate_ref": "EARLY"}).json()
    s2 = client.post("/v1/screenings", json={"job_ref": "HR-OPN-2026-0011", "candidate_ref": "LATE"}).json()
    late = client.get(f"/v1/screenings/{s2['screening_id']}").json()
    first = client.get(f"/v1/screenings/{s1['screening_id']}").json()
    assert late["duplicate_of"] == "EARLY"
    assert first["duplicate_of"] is None
