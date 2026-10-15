"""CV analysis: layout lines with boxes and confidence, page images, quote-to-box mapping."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.documents.extract import DISPLAY_DPI, extract
from app.documents.layout import boxes_for_quote, render_page
from app.ocr.base import NoneOCR
from app.ocr.fake import FakeOCR
from app.redaction.engine import redact
from tests.conftest import make_settings
from tests.test_documents import docx_bytes, png_bytes, scanned_pdf_bytes, text_pdf_bytes

LINES = [
    "Shift supervisor at a residential compound in Riyadh since 2019",
    "Supervised 8 guards on three shifts",
    "Valid security guard licence until 2027",
]


def test_text_pdf_layout_lines_match_text(tmp_path: Path):
    p = tmp_path / "cv.pdf"
    p.write_bytes(text_pdf_bytes(LINES))
    ex = extract(p, "pdf", NoneOCR(), make_settings(), "none")
    lay = ex.layout
    assert lay and lay["source"] == "pdf" and lay["dpi"] == DISPLAY_DPI and len(lay["pages"]) == 1
    assert [ln["t"] for ln in lay["lines"]] == ex.text.split("\n") == LINES
    page = lay["pages"][0]
    for ln in lay["lines"]:
        x0, y0, x1, y1 = ln["b"]
        assert 0 <= x0 < x1 <= page["w"] and 0 <= y0 < y1 <= page["h"] and ln["c"] == 1.0
    data, mime = render_page(p, "pdf", 0)
    assert mime == "image/png" and data[:8] == b"\x89PNG\r\n\x1a\n"


def test_ocr_layout_scaled_to_display_pixels(tmp_path: Path):
    p = tmp_path / "scan.pdf"
    p.write_bytes(scanned_pdf_bytes())
    ex = extract(p, "pdf", FakeOCR("حارس أمن منذ 2019\nرخصة سارية", 0.83), make_settings(), "fake")
    lay = ex.layout
    assert ex.method == "ocr:fake" and [ln["t"] for ln in lay["lines"]] == [
        "حارس أمن منذ 2019",
        "رخصة سارية",
    ]
    assert all(ln["c"] == 0.83 and len(ln["boxes"]) == 1 for ln in lay["lines"])
    w = lay["pages"][0]["w"]
    assert abs(w - 800 * DISPLAY_DPI / 72) < 2  # page width in display pixels
    assert all(0 <= ln["b"][2] <= w + 1 for ln in lay["lines"])


def test_image_layout_native_pixels(tmp_path: Path):
    p = tmp_path / "cv.png"
    p.write_bytes(png_bytes())
    ex = extract(p, "image", FakeOCR("إسعافات أولية", 0.7), make_settings(), "fake")
    assert ex.layout["source"] == "image" and ex.layout["pages"][0] == {"w": 300.0, "h": 100.0}
    data, mime = render_page(p, "image", 0)
    assert mime == "image/png"


@pytest.mark.skipif(not shutil.which("soffice"), reason="LibreOffice not installed")
def test_docx_gets_a_pdf_preview_with_layout(tmp_path: Path):
    p = tmp_path / "cv.docx"
    p.write_bytes(docx_bytes(["مشرف أمن في مجمع تجاري بالخبر", "خبرة 7 سنوات"]))
    ex = extract(p, "docx", NoneOCR(), make_settings(), "none")
    assert ex.method == "docx" and ex.preview_pdf and ex.preview_pdf[:4] == b"%PDF"
    assert ex.layout["source"] == "preview_pdf" and any(
        "مشرف أمن" in ln["t"] for ln in ex.layout["lines"]
    )


def test_quote_maps_to_line_and_ocr_segments():
    lay = {
        "lines": [
            {
                "t": "Shift supervisor since 2019",
                "boxes": [[0, 0, 10, 10, 1.0, "Shift supervisor since 2019"]],
            },
            {
                "t": "أتابع عمل 8 حراس أمن وأوزع المهام",
                "boxes": [
                    [0, 20, 5, 30, 0.9, "أتابع عمل 8 حراس أمن"],
                    [6, 20, 10, 30, 0.8, "وأوزع المهام"],
                ],
            },
            {"t": "اللغة العربية", "boxes": []},
        ]
    }
    assert boxes_for_quote("supervisor since 2019", lay) == [[0, -1]]
    assert boxes_for_quote("أتابع عمل 8 حراس أمن وأوزع المهام", lay) == [[1, 0], [1, 1]]
    assert boxes_for_quote("[الاسم] — أتابع عمل 8 حراس أمن", lay) == [[1, 0]]
    assert boxes_for_quote("not in the cv at all", lay) == [] and boxes_for_quote(None, lay) == []


def test_redaction_keeps_line_count_for_before_after_view():
    raw = "الاسم: فهد\nالجوال: 0551234567\nالبريد: a@b.com\nخبرة 9 سنوات"
    red = redact(raw, "فهد", use_nlp=False).text
    assert len(red.split("\n")) == len(raw.split("\n"))


def test_api_cv_layout_pages_file_and_quote_boxes(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from scripts.seed_data import JOBS
    from tests.conftest import API_KEY

    c = TestClient(create_app(make_settings(file_store=str(tmp_path / "files"))))
    with c:
        c.headers.update({"Authorization": f"Bearer {API_KEY}"})
        c.put("/v1/jobs/J", json=JOBS["HR-OPN-2026-0011"])
        c.put("/v1/candidates/C", json={"facts": {}, "answers": {"years_sup": 4}})
        pdf = text_pdf_bytes(LINES)
        assert (
            c.put(
                "/v1/candidates/C/cv", files={"file": ("cv.pdf", pdf, "application/pdf")}
            ).status_code
            == 200
        )
        doc = c.get("/v1/candidates/C/cv", params={"include_raw": True}).json()["document"]
        assert len(doc["layout"]["lines"]) == 3 and doc["page_images"] == ["pages/0"]
        assert doc["raw_text"].split("\n") == LINES and len(doc["redaction_pairs"]) == 3
        assert "raw_text" not in c.get("/v1/candidates/C/cv").json()["document"]
        r = c.get("/v1/candidates/C/cv/pages/0")
        assert r.status_code == 200 and r.headers["content-type"] == "image/png"
        assert c.get("/v1/candidates/C/cv/pages/5").status_code == 404
        f = c.get("/v1/candidates/C/cv/file")
        assert (
            f.status_code == 200
            and f.content == pdf
            and f.headers["content-type"] == "application/pdf"
        )
        ins = c.post(
            "/v1/documents/inspect",
            files={"file": ("x.pdf", pdf, "application/pdf")},
            data={"include_raw": "true"},
        ).json()
        assert ins["layout"]["lines"] and ins["page_images"][0].startswith("data:image/png;base64,")
