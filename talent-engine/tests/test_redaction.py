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
