from app.redaction.engine import redact
from app.redaction.names import name_regex

AR = """السيرة الذاتية — فهد العتيبي
الاسم: فهد سعد العتيبي
الجوال: 0551234567
البريد الإلكتروني: fahad.demo@example.com
رقم الهوية الوطنية: 1234567890
تاريخ الميلاد: 14/05/1992
الجنسية: السعودية
الجنس: ذكر
العنوان: حي النخيل، الرياض
مشرف أمن في شركة حراسات خاصة بالرياض من 2017 حتى الآن.
حاصل على رخصة حارس أمن سارية تنتهي 30/06/2027.
خبرة 9 سنوات في مجال الأمن والحراسة، أشرف على 14 فرد أمن.
"""


def test_arabic_cv_is_fully_redacted():
    r = redact(AR, name_hint="فهد سعد العتيبي", use_nlp=False)
    t = r.text
    assert "فهد" not in t and "العتيبي" not in t and "عتيبي" not in t
    assert "0551234567" not in t and "1234567890" not in t and "example.com" not in t
    assert "1992" not in t and "السعودية" not in t and "ذكر" not in t and "النخيل" not in t
    for tok in (
        "[الاسم]",
        "[الهاتف]",
        "[البريد]",
        "[الهوية]",
        "[تاريخ الميلاد]",
        "[الجنسية]",
        "[الجنس]",
        "[العنوان]",
    ):
        assert tok in t, tok
    # work history, licence expiry and experience numbers survive
    assert "2017" in t and "30/06/2027" in t and "9 سنوات" in t and "14 فرد أمن" in t
    assert r.report["phone"] == 1 and r.report["national_id"] == 1 and r.report["email"] == 1
    assert r.report["name"] >= 2 and r.report["dob"] == 1 and r.report["nationality"] >= 1


def test_idempotent_and_digits_normalised():
    once = redact(AR, name_hint="فهد العتيبي", use_nlp=False).text
    twice = redact(once, name_hint="فهد العتيبي", use_nlp=False).text
    assert once == twice
    r = redact("الجوال: ٠٥٥١٢٣٤٥٦٧ والهوية ١٠٠٠٠٠٠٠٠١", use_nlp=False)
    assert "[الهاتف]" in r.text and "[الهوية]" in r.text and "٠" not in r.text


def test_name_variants_and_prefix():
    rx = name_regex("أحمد الشهري")
    assert rx is not None
    assert rx.search("احمد") and rx.search("أَحمد") and rx.search("الشهري") and rx.search("شهري")
    assert not rx.search("محمود")
    assert name_regex("بن") is None and name_regex(None) is None


def test_english_cv_regex_only():
    en = """Omar Al-Mutairi — Software Developer
Name: Omar Al-Mutairi
Mobile: +966 55 123 4567
Email: omar.demo@example.com
National ID: 2345678901
Date of birth: 1998-03-02
Nationality: Saudi
Gender: Male
Address: Al Nakheel district, Riyadh
linkedin.com/in/omar-demo
Backend developer at a fintech startup in Riyadh since 2021.
"""
    r = redact(en, name_hint="Omar Al-Mutairi", use_nlp=False)
    t = r.text
    for bad in (
        "Omar",
        "Mutairi",
        "+966",
        "example.com",
        "2345678901",
        "1998",
        "Saudi",
        "Male",
        "linkedin",
    ):
        assert bad not in t, bad
    assert "since 2021" in t and "Riyadh" in t


def test_phone_formats():
    for s in (
        "+966501234567",
        "00966 50 123 4567",
        "050-123-4567",
        "0501234567",
        "+20 100 123 4567",
    ):
        assert "[الهاتف]" in redact(s, use_nlp=False).text, s


def test_age_and_gender_keywords_only():
    r = redact("العمر: 34 سنة. خبرة 15 سنة في الأمن. ذكر أنه عمل في الرياض.", use_nlp=False)
    assert "[العمر]" in r.text and "15 سنة" in r.text and "ذكر أنه" in r.text


def test_presidio_english_person_if_installed():
    import pytest

    pytest.importorskip("presidio_analyzer")
    pytest.importorskip("spacy")
    r = redact("References: John Smith, operations manager at Acme Security.", use_nlp=True)
    assert r.engine == "regex+presidio"
    assert "John Smith" not in r.text and "[الاسم]" in r.text


def test_ocr_style_alef_variants_in_keywords():
    r = redact(
        "ألعنوان: حي الورود، جدة\nألجنسية: مصري\nتأريخ الميلاد: 1990\nالإسم: سعد", use_nlp=False
    )
    assert (
        "[العنوان]" in r.text
        and "[الجنسية]" in r.text
        and "مصري" not in r.text
        and "[الاسم]" in r.text
    )


def test_id_keyword_keeps_newline():
    r = redact("رقم الهوية الوطنية 1200220022\nتاريخ الميلاد 14/05/1997", use_nlp=False)
    assert r.text == "رقم الهوية الوطنية [الهوية]\nتاريخ الميلاد [تاريخ الميلاد]"


def test_presidio_leaves_arabic_lines_alone():
    import pytest

    pytest.importorskip("presidio_analyzer")
    text = "أشرف على فريق من 14 فرد أمن في ثلاث مواقع تجارية\nحاصل على شهادة إسعافات أولية معتمدة\nReference: John Smith"
    r = redact(text, use_nlp=True)
    assert "أشرف على فريق من 14 فرد أمن" in r.text and "إسعافات أولية" in r.text
    assert "John Smith" not in r.text


def test_dates_with_spaces_and_year_first():
    r = redact("تاريخ الميلاد: 1992 / 05 / 14\nمن 01/03/2017 حتى 2024", use_nlp=False)
    assert "[تاريخ الميلاد]" in r.text and "1992" not in r.text and "01/03/2017" in r.text


def test_split_dob_line_is_fully_scrubbed():
    r = redact("05/1992 :تاريخ الميلاد14/\nرخصة سارية حتى 2027", use_nlp=False)
    assert (
        "1992" not in r.text
        and "14" not in r.text
        and "[تاريخ الميلاد]" in r.text
        and "2027" in r.text
    )


# ----------------------------------------------------------------------------- round 3: no leak
def _every_synthetic_line() -> list[str]:
    from tests.test_pdftext import all_cv_lines

    return all_cv_lines()


def _known_secrets() -> list[str]:
    """The fictional e-mails, phones and IDs that the synthetic CVs carry."""
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.cv_texts import CV_TEXTS
    from scripts.make_cvs import contact_block

    out = []
    for ref, cv in CV_TEXTS.items():
        for ln in contact_block(ref, cv["lines"][0])[1]:
            v = ln.split(":", 1)[-1].strip()
            if "@" in v or sum(ch.isdigit() for ch in v) >= 9:
                out.append(v)
    assert len(out) >= 40
    return out


def test_email_broken_by_a_pdf_writer_is_still_redacted():
    from app.redaction.engine import leak_check

    for broken in (
        "البريد الإلكتروني: demo.2001@example com.",
        "البريد الإلكتروني demo.2001@example com",
        "demo .2001 @ example . com",
        "Email: demo.2022@example.com",
        "رقم الهوية 1200 1200 12",
        "الجوال 052 001 1002",
    ):
        r = redact(broken, use_nlp=False)
        assert leak_check(r.text) == [], (broken, r.text)
        assert "demo" not in r.text and "example" not in r.text and "2001" not in r.text
    # years, dates of work and short numbers stay
    r = redact("من 2017 حتى 2026، رخصة تنتهي 30/06/2027، فريق من 14 فردًا", use_nlp=False)
    assert (
        "2017" in r.text and "30/06/2027" in r.text and "14" in r.text and not r.report.get("guard")
    )


def test_no_email_phone_or_id_of_any_synthetic_cv_reaches_the_model():
    """Every line of the 20 synthetic CVs and the gold set, as written and as a PDF writer
    prints it (visual order, then reconstructed): after redaction nothing that looks like an
    address or a long number is left, and none of the fictional secrets survives."""
    from bidi.algorithm import get_display

    from app.documents.pdftext import logical_text
    from app.redaction.engine import leak_check

    secrets = _known_secrets()
    lines = _every_synthetic_line()
    texts = ["\n".join(lines), "\n".join(logical_text(get_display(ln)) for ln in lines)]
    for text in texts:
        r = redact(text, use_nlp=False)
        assert leak_check(r.text) == []
        squeezed = r.text.replace(" ", "")
        for s in secrets:
            assert s not in r.text and s.replace(" ", "") not in squeezed, s
    # the sweep is a safety net, not the normal path: the patterns catch them first
    assert redact(texts[0], use_nlp=False).report.get("guard", 0) == 0


def test_leak_check_catches_what_a_model_must_never_see():
    from app.redaction.engine import leak_check

    assert leak_check("مرحبا demo@example com") == ["demo@example"]
    assert leak_check("الهوية 1 2 0 0 1 2 0 0 1 2") and leak_check("tel 05-2001-1002")
    assert leak_check("خبرة 9 سنوات من 2017 حتى 2026") == []
    assert leak_check(None) == [] and leak_check("") == []


def test_reprocess_recovers_the_name_hint_from_the_earlier_redaction():
    """The engine keeps no name: when a stored CV is re-extracted, the name the host gave at
    upload time is read back from what the earlier redaction replaced (round 4 review)."""
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.reprocess_cvs import recover_name_hints

    raw = "السيرة الذاتية — فهد العتيبي\nالاسم: فهد سعد العتيبي\nمشرف أمن منذ 2017"
    first = redact(raw, name_hint="فهد سعد العتيبي", use_nlp=False).text
    hints = recover_name_hints(raw, first)
    assert any("العتيبي" in h for h in hints), hints
    again = redact(raw, name_hint=" ".join(hints), use_nlp=False).text
    assert "فهد" not in again and "العتيبي" not in again and "2017" in again
    assert recover_name_hints(raw, "x") == []  # line counts differ: nothing guessed


def test_free_text_answer_redaction_keeps_the_evidence():
    """Final QA: the redaction now runs over free-text answers before the judge. Numbers that are
    evidence (team sizes, years, durations) must survive; only personal data goes."""
    from app.redaction.engine import redact

    keep = [
        "مشرف وردية في مجمع سكني كبير بالرياض منذ 2019، أتابع 8 حراس.",
        "عندي 10 سنوات خبرة، أشرف على 8 حراس منذ 2019 في مجمع سكني",
        "مشرف أمن من 2015 إلى 2024، فريق من 12 فرد، رخصة سارية حتى 2027",
        "حللت بيانات شكاوى العملاء (40 ألف سجل) بـ SQL وPython لمعرفة أسباب التأخير؛ انخفض زمن الاستجابة 30% خلال ثلاثة أشهر.",
        "Security shift supervisor at a shopping mall in Cairo, 2015–2023.",
    ]
    for t in keep:
        assert redact(t).text == t, t
    pii = "للتواصل 0520202002 أو demo.majed@example.com، هويتي 1000009901، مواليد 20/06/1997"
    out = redact(pii).text
    assert out == "للتواصل [الهاتف] أو [البريد]، هويتي [الهوية]، مواليد [تاريخ الميلاد]"
