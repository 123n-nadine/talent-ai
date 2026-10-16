"""Consent withdrawn (OPEN_QUESTIONS #21, default decided by Nadine on 2026-10-16): the candidate
leaves the ranking at once and shows in «مستبعد: سحب الموافقة» with no score and no details; the
CV documents and their files, the structured profile, the talent-pool index and every result are
erased from the engine; only the reference stays."""

from __future__ import annotations

from sqlalchemy import func, select

from app.documents.store import FileStore
from app.pipeline import runner
from app.storage.models import (
    AuditEvent,
    Candidate,
    CriterionResult,
    Document,
    Embedding,
    Profile,
    Screening,
)
from tests.test_documents import text_pdf_bytes

SEC = "HR-OPN-2026-0011"
REF = "HR-APP-2026-2002"


def _db(client):
    return client.app.state.sessionmaker()


def _cv(client, ref: str, lines: list[str] | None = None, pdf: bytes | None = None):
    pdf = pdf or text_pdf_bytes(
        lines or ["Shift supervisor since 2019 supervising 8 guards", "Valid licence"]
    )
    r = client.put(f"/v1/candidates/{ref}/cv", files={"file": ("cv.pdf", pdf, "application/pdf")})
    assert r.status_code == 200, r.text
    return r.json()["document"]


def _withdraw(client, ref: str):
    c = client.get(f"/v1/candidates/{ref}").json()
    r = client.put(
        f"/v1/candidates/{ref}",
        json={**{k: c[k] for k in ("id_token", "facts", "answers")}, "consent": False},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _count(db, model, **where) -> int:
    q = select(func.count()).select_from(model)
    for k, v in where.items():
        q = q.where(getattr(model, k) == v)
    return db.scalar(q) or 0


def test_withdrawn_consent_erases_the_ai_data_and_leaves_the_ranking(client, seeded, sec_job):
    doc = _cv(client, REF)
    sid = client.post(
        "/v1/screenings", json={"job_ref": SEC, "candidate_ref": REF, "force": True}
    ).json()["screening_id"]
    assert client.get(f"/v1/screenings/{sid}").json()["status"] in ("completed", "needs_review")
    store = FileStore(client.app.state.settings.file_store)
    assert store.path_for(doc["sha256"]).exists()
    before = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert any(x["candidate_ref"] == REF for x in before["ranked"])
    with _db(client) as db:
        cid = db.scalar(select(Candidate.id).where(Candidate.external_ref == REF))
        assert _count(db, Embedding, candidate_id=cid) == 1

    out = _withdraw(client, REF)
    assert (
        out["consent"] is False and out["consent_withdrawn_at"] and out["withdrawn_from"] == [SEC]
    )
    assert out["erased"]["documents"] == 1 and out["erased"]["screenings"] == 2
    assert out["erased"]["embeddings"] == 1 and out["erased"]["files"] >= 1

    # nothing the AI made of the application is left
    c = client.get(f"/v1/candidates/{REF}").json()
    assert c["facts"] == {} and c["answers"] == {} and c["id_token"] is None
    assert c["documents"] == [] and c["screenings"] == []
    assert not store.path_for(doc["sha256"]).exists()
    assert client.get(f"/v1/screenings/{sid}").status_code == 404
    with _db(client) as db:
        for model in (Document, Profile, Embedding, Screening):
            assert _count(db, model, candidate_id=cid) == 0, model.__name__
        assert _count(db, CriterionResult, screening_id=sid) == 0
    # the audit trail keeps what happened, not what the AI found
    events = client.get("/v1/audit", params={"ref": REF}).json()["events"]
    assert any(e["action"] == "screening.completed" for e in events)
    for e in events:
        assert "score" not in e["payload"] and "sha256" not in e["payload"], e
        if e["action"] != "candidate.consent_withdrawn":
            assert e["payload"] == {"erased": True}, e

    # out of the ranking at once, in its own group with no score and no details
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert all(x["candidate_ref"] != REF for x in rk["ranked"])
    assert rk["ranked_total"] == before["ranked_total"] - 1 and rk["total"] == before["total"]
    others = [x for g, xs in rk["groups"].items() if g != "consent_withdrawn" for x in xs]
    assert all(x["candidate_ref"] != REF for x in others)
    (item,) = rk["groups"]["consent_withdrawn"]
    assert item["candidate_ref"] == REF and item["withdrawn_at"]
    assert item["score"] is None and item["band"] is None and item["flags"] == []
    assert item["reason_ar"].startswith("مستبعد: سحب الموافقة")

    # no new processing of any kind
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": REF, "force": True})
    assert r.status_code == 409
    r = client.put(
        f"/v1/candidates/{REF}/cv",
        files={"file": ("cv.pdf", text_pdf_bytes(["x"]), "application/pdf")},
    )
    assert r.status_code == 409
    r = client.post(f"/v1/jobs/{SEC}/rescreen", params={"force": True})
    assert REF in r.json()["skipped"] or all(REF not in q for q in r.json()["queued"])

    # the talent pool lists the reference as excluded, with the reason only
    assert (
        client.put(
            "/v1/jobs/HR-OPN-2026-0099", json={**sec_job, "title": "مشرف أمن — جدة"}
        ).status_code
        == 200
    )
    pool = client.post("/v1/talent-pool/search", json={"job_ref": "HR-OPN-2026-0099", "limit": 50})
    assert pool.status_code == 200, pool.text
    ex = {x["candidate_ref"]: x for x in pool.json()["excluded"]}
    assert ex[REF]["reason"] == "consent_withdrawn" and ex[REF]["details"] == []
    assert ex[REF]["previous_job_ref"] == SEC
    assert REF not in [x["candidate_ref"] for x in pool.json()["suggestions"]]


def test_withdrawing_the_original_promotes_the_later_copy(client, seeded):
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert "HR-APP-2026-2016" in {x["candidate_ref"] for x in rk["groups"]["duplicate"]}
    out = _withdraw(client, "HR-APP-2026-2015")
    assert out["erased"]["promoted"] == ["HR-APP-2026-2016"]
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert not rk["groups"]["duplicate"]
    s = client.get(f"/v1/screenings/{seeded['HR-APP-2026-2016']}").json()
    assert s["duplicate_of"] is None and "duplicate" not in s["flags"]
    placed = {x["candidate_ref"] for x in rk["ranked"]} | {
        x["candidate_ref"] for xs in rk["groups"].values() for x in xs
    }
    assert "HR-APP-2026-2016" in placed


def test_a_file_shared_by_two_candidates_stays_until_the_last_one_goes(client, seeded):
    pdf = text_pdf_bytes(["Shared CV file", "Security supervisor 2018-2025"])
    a = _cv(client, "HR-APP-2026-2003", pdf=pdf)
    b = _cv(client, "HR-APP-2026-2004", pdf=pdf)
    assert a["sha256"] == b["sha256"]
    store = FileStore(client.app.state.settings.file_store)
    _withdraw(client, "HR-APP-2026-2003")
    assert store.path_for(a["sha256"]).exists()
    assert client.get("/v1/candidates/HR-APP-2026-2004/cv/pages/0").status_code == 200
    assert client.delete("/v1/candidates/HR-APP-2026-2004/cv").json()["removed"] == 1
    assert not store.path_for(a["sha256"]).exists()


def test_deleting_a_candidate_also_removes_the_cv_file(client, seeded):
    doc = _cv(client, "HR-APP-2026-2005", ["Only this candidate has this file"])
    store = FileStore(client.app.state.settings.file_store)
    assert store.path_for(doc["sha256"]).exists()
    r = client.delete("/v1/candidates/HR-APP-2026-2005")
    assert r.status_code == 200 and r.json()["removed"]["documents"] == 1
    assert not store.path_for(doc["sha256"]).exists()
    events = client.get("/v1/audit", params={"ref": "HR-APP-2026-2005"}).json()["events"]
    assert events[0]["action"] == "candidate.deleted"
    assert all(e["payload"] == {"erased": True} for e in events[1:])


def test_a_run_that_meets_a_withdrawal_keeps_nothing(client, seeded, monkeypatch):
    """The worker locks the candidate before it writes; a withdrawal that came first wins."""
    sid = client.post(
        "/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2006", "force": True}
    ).json()["screening_id"]
    with _db(client) as db:
        s = db.get(Screening, sid)
        s.status, s.score = "queued", None
        for r in list(s.criteria):
            db.delete(r)
        db.commit()

    def completed_events() -> int:
        with _db(client) as db:
            return _count(db, AuditEvent, ref="HR-APP-2026-2006", action="screening.completed")

    done_before = completed_events()
    monkeypatch.setattr(runner, "_still_consented", lambda db, cid: False)
    settings = client.app.state.settings
    with _db(client) as db:
        assert runner.run_screening(db, settings, sid, deliver=False) is None
    with _db(client) as db:
        s = db.get(Screening, sid)
        assert s.score is None and not s.criteria and s.status != "completed"
        cid = s.candidate_id
        assert _count(db, Embedding, candidate_id=cid) == 1  # the earlier run's, untouched
    assert completed_events() == done_before
    # a screening erased before it ran is skipped quietly
    _withdraw(client, "HR-APP-2026-2006")
    with _db(client) as db:
        assert runner.run_screening(db, settings, sid, deliver=False) is None
    assert runner.execute_with_retries(client.app.state.sessionmaker, settings, sid) == "erased"


def test_consent_given_again_starts_afresh(client, seeded):
    c = client.get("/v1/candidates/HR-APP-2026-2007").json()
    keep = {k: c[k] for k in ("id_token", "facts", "answers")}
    _withdraw(client, "HR-APP-2026-2007")
    r = client.put("/v1/candidates/HR-APP-2026-2007", json={**keep, "consent": True})
    assert r.json()["consent"] is True and r.json()["consent_withdrawn_at"] is None
    assert r.json()["withdrawn_from"] == [] and r.json()["facts"] == keep["facts"]
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2007"})
    assert r.status_code == 202 and r.json()["created"] is True
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert not rk["groups"]["consent_withdrawn"]


def test_a_candidate_sent_without_consent_is_kept_bare(client, sec_job):
    client.put(f"/v1/jobs/{SEC}", json=sec_job)
    r = client.put(
        "/v1/candidates/NO-CONSENT",
        json={
            "id_token": "tok",
            "facts": {"age": 30},
            "answers": {"edu": "ثانوي"},
            "consent": False,
        },
    )
    out = r.json()
    assert out["consent"] is False and out["facts"] == {} and out["answers"] == {}
    assert out["id_token"] is None and out["consent_withdrawn_at"] is None and "erased" not in out
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "NO-CONSENT"})
    assert r.status_code == 409
    assert not client.get(f"/v1/jobs/{SEC}/ranking").json()["groups"]["consent_withdrawn"]


def test_withdrawal_is_idempotent(client, seeded):
    _withdraw(client, "HR-APP-2026-2008")
    again = _withdraw(client, "HR-APP-2026-2008")
    assert "erased" not in again and again["consent"] is False
    rk = client.get(f"/v1/jobs/{SEC}/ranking").json()
    assert [x["candidate_ref"] for x in rk["groups"]["consent_withdrawn"]] == ["HR-APP-2026-2008"]
