"""Text of Arabic PDFs comes back in logical order, with every e-mail, number, date and full stop
where it belongs (round 3 review: a dot of an e-mail landed at the end of the line, a number was
glued to the word before it)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymupdf
import pytest
from bidi.algorithm import get_display

from app.documents.extract import extract
from app.documents.pdftext import group_rows, logical_text, page_chars, row_text
from app.ocr.registry import NoneOCR
from app.pipeline.stages.profile import parse_date, years_between
from app.scoring.rubric import years_in_quote
from tests.conftest import make_settings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.cv_texts import CV_TEXTS  # noqa: E402
from scripts.make_cvs import contact_block  # noqa: E402

DEJAVU = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def all_cv_lines() -> list[str]:
    """Every line of the synthetic CVs (bodies and contact blocks) and of the gold set."""
    import json

    lines: list[str] = []
    for ref, cv in CV_TEXTS.items():
        lines += cv["lines"]
        lines += contact_block(ref, cv["lines"][0])[1]
    gold = Path(__file__).resolve().parent.parent / "eval" / "gold"
    for p in gold.glob("*.json"):
        data = json.load(open(p, encoding="utf-8"))
        for a in data["applicants"] if isinstance(data, dict) else data:
            lines += a.get("cv_lines") or []
    return [ln for ln in lines if ln.strip()]


def visual_pdf_bytes(pages: list[list[str]]) -> bytes:
    """Pages written the way Word and LibreOffice write Arabic: glyphs in visual order."""
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        y = 60
        for line in lines:
            page.insert_text(
                (40, y), get_display(line), fontsize=10, fontfile=str(DEJAVU), fontname="dv"
            )
            y += 15
    return doc.tobytes()


def test_inverse_of_the_bidi_display_on_every_synthetic_line():
    """python-bidi turns logical text into what is printed; our reconstruction must give the
    logical text back, on every line of the 20 synthetic CVs and the 50 gold applicants."""
    lines = all_cv_lines()
    assert len(lines) > 300
    bad = [ln for ln in lines if logical_text(get_display(ln)) != ln]
    assert not bad, bad[:10]


def test_mirrored_brackets_and_mixed_lines():
    assert (
        logical_text(get_display("شهادة (إسعافات أولية) من 2024"))
        == "شهادة (إسعافات أولية) من 2024"
    )
    assert logical_text(get_display("Name: فهد العتيبي"), base="L") == "Name: فهد العتيبي"
    assert (
        logical_text(get_display("الخبرة: 9 سنوات (2017–2026).")) == "الخبرة: 9 سنوات (2017–2026)."
    )
    assert logical_text("Hello world") == "Hello world"


@pytest.mark.skipif(not DEJAVU.exists(), reason="needs DejaVu Sans (an Arabic-capable font)")
def test_visual_order_pdf_comes_back_logical(tmp_path: Path):
    lines = [
        "السيرة الذاتية — فهد العتيبي",
        "البريد الإلكتروني: demo.2001@example.com",
        "الجوال: 0520011002",
        "تاريخ الميلاد: 14/05/1992",
        "مشرف أمن في شركة حراسات خاصة بالرياض من 2017 حتى الآن.",
        "أشرف على فريق من 14 فرد أمن في ثلاث مواقع تجارية.",
        "إجمالي الخبرة في مجال الأمن والحراسة 9 سنوات.",
    ]
    english = [
        "CV — Abdulaziz Al-Otaibi",
        "Name: فهد العتيبي",
        "Email: demo.2022@example.com",
        "Arabic (native), English",
    ]
    p = tmp_path / "visual.pdf"
    p.write_bytes(visual_pdf_bytes([lines, english]))
    ex = extract(p, "pdf", NoneOCR(), make_settings(), "none")
    assert ex.status == "ready"
    got = ex.text.split("\n")
    assert got == lines + english
    assert [
        ln["t"] for ln in ex.layout["lines"]
    ] == lines + english  # the boxes carry the same text


def test_row_reconstruction_from_character_boxes():
    """Characters placed as on paper (left to right), one of them a lam-alef ligature with no box
    of its own and a phantom space over a real dot, as PyMuPDF reports them."""

    def ch(c, x0, x1, yb=20.0):
        return {"c": c, "x0": x0, "x1": x1, "y0": yb - 8, "y1": yb + 2, "yb": yb, "size": 10.0}

    visual = get_display("الاسم: demo.2001@example.com")
    row = [ch(c, 10 + i * 6, 16 + i * 6) for i, c in enumerate(visual)]
    assert row_text(row) == "الاسم: demo.2001@example.com"
    # the dot drawn as its own glyph under a phantom space
    i = visual.index(".")
    row.append(ch(" ", row[i]["x0"], row[i]["x1"]))
    assert row_text(row) == "الاسم: demo.2001@example.com"
    # two rows by baseline
    rows = group_rows(row + [ch("x", 10, 16, yb=40.0)])
    assert len(rows) == 2 and row_text(rows[1]) == "x"


def test_generated_arabic_pdf_if_present():
    p = Path("data/cvs/HR-APP-2026-2001.pdf")
    if not p.exists():
        pytest.skip("run `make cvs` first")
    ex = extract(p, "pdf", NoneOCR(), make_settings(), "none")
    lines = ex.text.split("\n")
    assert "البريد الإلكتروني: demo.2001@example.com" in lines
    assert "أشرف على فريق من 14 فرد أمن في ثلاث مواقع تجارية." in lines
    assert "مشرف أمن في شركة حراسات خاصة بالرياض من 2017 حتى الآن." in lines
    assert "إجمالي الخبرة في مجال الأمن والحراسة 9 سنوات." in lines
    assert "تاريخ الميلاد: 14/05/1992" in lines and "الجوال: 0520011002" in lines
    chars = group_rows(page_chars(pymupdf.open(p)[0]))
    assert any(row_text(r).startswith("الاسم:") for r in chars)


def test_years_read_from_reconstructed_lines():
    """The durations the code reads from a CV line are right once the line is in order."""
    assert years_in_quote("إجمالي الخبرة في مجال الأمن والحراسة 9 سنوات.") == 9.0
    assert years_in_quote("أشرف على فريق من 14 فرد أمن في ثلاث مواقع تجارية.") is None
    from datetime import UTC, datetime

    now = datetime(2026, 10, 16, tzinfo=UTC)
    start = parse_date("2017", now)
    assert years_between(start, parse_date("حتى الآن", now)) == 9.8
