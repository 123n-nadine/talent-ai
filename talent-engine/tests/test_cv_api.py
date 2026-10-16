from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import API_KEY, make_settings
from tests.test_documents import scanned_pdf_bytes, text_pdf_bytes

SEC = "HR-OPN-2026-0011"


def _client(tmp_path, **overrides):
    settings = make_settings(file_store=str(tmp_path / "files"), ocr_provider="fake", **overrides)
    c = TestClient(create_app(settings))
    c.__enter__()
    c.headers.update({"Authorization": f"Bearer {API_KEY}", "X-Talent-Actor": "pytest"})
    return c


def test_upload_replaces_stale_and_shows_in_screening(tmp_path, seeded, client):
    sid = seeded["HR-APP-2026-2002"]
    before = client.get("/v1/candidates/HR-APP-2026-2002").json()["data_hash"]
    pdf = text_pdf_bytes(
        [
            "Sultan Al-Harbi",
            "Mobile: 0551234567",
            "Shift supervisor since 2019 supervising 8 guards",
            "Valid licence",
        ]
    )
    r = client.put(
        "/v1/candidates/HR-APP-2026-2002/cv",
        files={"file": ("cv.pdf", pdf, "application/pdf")},
        data={"name_hint": "Sultan Al-Harbi"},
    )
    assert r.status_code == 200, r.text
    d = r.json()["document"]
    assert (
        d["status"] == "ready"
        and d["extraction_method"] == "pdf_text"
        and d["name_hint_used"] is True
    )
    assert (
        "[الهاتف]" in d["redacted_text"]
        and "Sultan" not in d["redacted_text"]
        and "0551234567" not in d["redacted_text"]
    )
    assert r.json()["data_hash"] != before
    s = client.get(f"/v1/screenings/{sid}").json()
    assert s["current"] is False and s["stale_reason"] == "data_changed"
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2002"})
    s = client.get(f"/v1/screenings/{r.json()['screening_id']}").json()
    stages = {st["key"]: st for st in s["stages"]}
    assert stages["cv_text"]["status"] == "done" and "نص PDF مباشر" in stages["cv_text"]["note"]
    assert stages["redaction"]["status"] == "done" and stages["profile"]["status"] == "skipped"
    assert s["cv"]["status"] == "ready" and "redacted_text" in s["cv"] and s["score"] == 81.5
    cv = client.get("/v1/candidates/HR-APP-2026-2002/cv").json()["document"]
    assert cv["sha256"] == d["sha256"]
    r = client.delete("/v1/candidates/HR-APP-2026-2002/cv")
    assert (
        r.json()["removed"] == 1
        and client.get("/v1/candidates/HR-APP-2026-2002/cv").status_code == 404
    )


def test_corrupt_cv_never_fails_the_screening(seeded, client):
    r = client.put(
        "/v1/candidates/HR-APP-2026-2013/cv",
        files={"file": ("cv.pdf", b"%PDF-1.4\n\x00\x00broken" * 50, "application/pdf")},
    )
    assert r.status_code == 200 and r.json()["document"]["status"] == "unreadable"
    r = client.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "HR-APP-2026-2013"})
    s = client.get(f"/v1/screenings/{r.json()['screening_id']}").json()
    assert s["status"] == "completed" and "cv_unreadable" in s["flags"] and s["score"] == 65.0
    stages = {st["key"]: st for st in s["stages"]}
    assert stages["cv_text"]["status"] == "failed" and "غير مقروء" in stages["cv_text"]["note"]


def test_low_ocr_confidence_needs_review(tmp_path, sec_job):
    c = _client(tmp_path, fake_ocr_confidence=0.55)
    c.put(f"/v1/jobs/{SEC}", json=sec_job)
    c.put(
        "/v1/candidates/C-S",
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
    r = c.put(
        "/v1/candidates/C-S/cv",
        files={"file": ("scan.pdf", scanned_pdf_bytes(), "application/pdf")},
    )
    d = r.json()["document"]
    assert (
        d["status"] == "ready"
        and d["extraction_method"] == "ocr:fake"
        and d["ocr_confidence"] == 0.55
    )
    r = c.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "C-S"})
    s = c.get(f"/v1/screenings/{r.json()['screening_id']}").json()
    assert (
        s["ai_status"] == "Needs Review"
        and "low_ocr_confidence" in s["flags"]
        and s["score"] == 81.5
    )
    rk = c.get(f"/v1/jobs/{SEC}/ranking").json()
    assert [x["candidate_ref"] for x in rk["groups"]["needs_review"]] == ["C-S"]
    # an HR override does not silently clear the OCR review flag
    r = c.post(
        f"/v1/screenings/{s['screening_id']}/override",
        json={"criterion_key": "first_aid", "level": 50, "reason": "شهادة قديمة", "by": "hr"},
    )
    assert r.json()["ai_status"] == "Needs Review"
    c.__exit__(None, None, None)


def test_inspect_stores_nothing(tmp_path, client):
    n = len(client.get("/v1/candidates").json()["candidates"])
    pdf = text_pdf_bytes(
        ["Name: Ahmed Hassan", "Phone 0501234567", "Security supervisor 2015-2023"]
    )
    r = client.post(
        "/v1/documents/inspect",
        files={"file": ("x.pdf", pdf, "application/pdf")},
        data={"name_hint": "Ahmed Hassan", "include_raw": "true"},
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["stored"] is False and j["status"] == "ready" and "[الهاتف]" in j["redacted_text"]
    assert "Ahmed" not in j["redacted_text"] and "Ahmed" in j["raw_text"]
    assert len(client.get("/v1/candidates").json()["candidates"]) == n
    r = client.post(
        "/v1/documents/inspect",
        files={"file": ("x.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert r.status_code == 422


def test_upload_size_limit(tmp_path, sec_job):
    c = _client(tmp_path, max_upload_mb=1)
    c.put("/v1/candidates/C-B", json={"facts": {}, "answers": {}})
    big = b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 1)
    r = c.put("/v1/candidates/C-B/cv", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 422 and "MB" in r.text
    c.__exit__(None, None, None)


def test_settings_show_ocr_readiness(client):
    s = client.get("/v1/settings").json()
    assert (
        s["ocr_provider"] == "fake"
        and s["ocr_ready"] is True
        and "paddle_cpu" in s["ocr_providers"]
    )


def test_reprocessed_cv_is_new_input(seeded, client):
    pdf = text_pdf_bytes(
        [
            "Shift supervisor since 2019 at a large residential compound in Riyadh",
            "Valid security guard licence and recent first aid training",
        ]
    )
    h1 = client.put(
        "/v1/candidates/HR-APP-2026-2004/cv", files={"file": ("cv.pdf", pdf, "application/pdf")}
    ).json()["data_hash"]
    h2 = client.put(
        "/v1/candidates/HR-APP-2026-2004/cv",
        files={"file": ("cv.pdf", pdf, "application/pdf")},
        data={"name_hint": "Shift"},
    ).json()["data_hash"]
    assert h1 != h2  # same file, different redaction outcome -> different input


def test_weak_ocr_lines_are_never_evidence(tmp_path, sec_job):
    """Round 3 review: a line read at 69% confidence had been highlighted as evidence. A line
    under OCR_MIN_CONFIDENCE is taken out of the text before the model and before any quote
    check; the same line read well is accepted."""
    from app.llm.fake import FakeLLM
    from app.pipeline import runner
    from app.pipeline.stages.cv_text import WEAK_MARK

    quote = "أشرف على فريق من 8 حراس في الوردية"

    def screen(text: str) -> dict:
        c = _client(tmp_path, fake_ocr_text=text, fake_ocr_confidence=0.95)
        c.put(f"/v1/jobs/{SEC}", json=sec_job)
        c.put(
            "/v1/candidates/C-W",
            json={
                "facts": {"nationality": "السعودية", "height_cm": 181, "weight_kg": 79, "age": 29},
                "answers": {"years_sec": 6, "licence": "سارية", "languages": ["العربية"]},
            },
        )
        r = c.put(
            "/v1/candidates/C-W/cv",
            files={"file": ("scan.pdf", scanned_pdf_bytes(), "application/pdf")},
        )
        assert r.status_code == 200, r.text
        sid = c.post("/v1/screenings", json={"job_ref": SEC, "candidate_ref": "C-W"}).json()[
            "screening_id"
        ]
        with c.app.state.sessionmaker() as db:  # run again with a provider that quotes the CV
            from app.storage.models import Screening

            row = db.get(Screening, sid)
            row.status = "queued"
            for cr in list(row.criteria):
                db.delete(cr)
            db.commit()
            s = runner.run_screening(
                db,
                c.app.state.settings,
                sid,
                provider=FakeLLM({"supervision": (100, quote)}),
                deliver=False,
            )
            assert s is not None and s.status in ("completed", "needs_review")
        out = c.get(f"/v1/screenings/{sid}").json()
        c.__exit__(None, None, None)
        return out

    weak = screen(f"حارس أمن في مجمع تجاري منذ 2019\n~{quote}\nرخصة حارس أمن سارية")
    sup = next(x for x in weak["criteria"] if x["key"] == "supervision")
    assert (
        sup["cv_level"] is None and sup["cv_quote"] is None and "quote_not_found" in weak["flags"]
    )
    assert weak["versions"]["weak_lines"] == [1]
    assert weak["cv"]["redacted_text"].split("\n")[1] == WEAK_MARK and weak["cv"]["weak_lines"] == [
        1
    ]
    assert (
        quote not in weak["cv"]["redacted_text"] and "supervision" not in weak["cv"]["quote_boxes"]
    )
    stage = next(st for st in weak["stages"] if st["key"] == "cv_text")
    assert "مستبعد" in stage["note"] and "weak line" in stage["note_en"]
    assert "low_ocr_confidence" not in weak["flags"]  # the page average is still above 0.80

    good = screen(f"حارس أمن في مجمع تجاري منذ 2019\n{quote}\nرخصة حارس أمن سارية")
    sup = next(x for x in good["criteria"] if x["key"] == "supervision")
    assert (
        sup["cv_level"] == 100 and sup["cv_quote"] == quote and good["versions"]["weak_lines"] == []
    )
    assert "supervision" in good["cv"]["quote_boxes"]
