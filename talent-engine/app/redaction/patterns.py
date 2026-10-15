"""Regex patterns for Saudi/Arabic/English personal data (stage 4). Names come from a hint."""

from __future__ import annotations

import re

TOKENS = {
    "NAME": "[الاسم]",
    "PHONE": "[الهاتف]",
    "EMAIL": "[البريد]",
    "NATIONAL_ID": "[الهوية]",
    "NATIONALITY": "[الجنسية]",
    "GENDER": "[الجنس]",
    "DOB": "[تاريخ الميلاد]",
    "AGE": "[العمر]",
    "ADDRESS": "[العنوان]",
    "URL": "[رابط]",
}

# word boundaries that work for Arabic as well as Latin letters
B0 = r"(?<![\w؀-ۿ])"
B1 = r"(?![\w؀-ۿ])"
SEP = r"\s*[:：\-–]?\s*"


def kw(*words: str) -> str:
    """Alternation of Arabic keywords where alef and ta-marbuta variants all match (OCR confuses them)."""
    outs = [
        "".join("[اأإآ]" if ch in "اأإآ" else ("[هة]" if ch in "هة" else ch) for ch in w)
        for w in words
    ]
    return "(?:" + "|".join(outs) + ")"


EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+", re.UNICODE)
URL = re.compile(
    r"(?:https?://|www\.)\S+|(?:linkedin\.com|twitter\.com|x\.com|facebook\.com|instagram\.com)/\S+",
    re.I,
)
# Saudi mobiles (05x / +966 5x / 00966 5x) with optional spaces or dashes, and generic international numbers
PHONE = re.compile(
    r"(?<!\d)(?:\+?966|00966|0)[\s\-]?5\d(?:[\s\-]?\d){7}(?!\d)"
    r"|(?<!\d)\+\d{1,3}[\s\-]?\d(?:[\s\-]?\d){7,11}(?!\d)"
    r"|(?<!\d)0\d{2}[\s\-]?\d{3}[\s\-]?\d{4}(?!\d)"
)
NATIONAL_ID = re.compile(r"(?<!\d)[12]\d{9}(?!\d)")
ID_KEYWORD_LINE = re.compile(
    rf"(رقم\s+{kw('الهوية', 'الإقامة', 'البطاقة')}(?:\s+{kw('الوطنية')})?|{kw('الهوية')}\s+{kw('الوطنية')}|{kw('الإقامة')}|national\s+id|iqama|id\s+(?:no|number))"
    rf"{SEP}(?P<val>[\d \-]{{6,20}})",
    re.I,
)
DATE = r"\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)?\d{2}|(?:19|20)\d{2}[/\-.]\d{1,2}[/\-.]\d{1,2}"
DOB_KEYWORD_LINE = re.compile(
    rf"(تاريخ\s+{kw('الميلاد', 'الولادة')}|{kw('المواليد', 'مواليد')}|date\s+of\s+birth|birth\s*date|d\.?o\.?b\.?|born(?:\s+on)?)"
    rf"{SEP}(?P<val>[^\n]{{0,25}}?(?:{DATE}|(?:19|20)\d{{2}}))",
    re.I,
)
DOB_KEYWORD = re.compile(
    rf"(تاريخ\s+{kw('الميلاد', 'الولادة')}|{kw('المواليد', 'مواليد')}|date\s+of\s+birth|birth\s*date|\bd\.?o\.?b\b)",
    re.I,
)
DOB_DIGITS = re.compile(r"\d[\d/\-. ]*\d|\d")
# full day-month-year dates with a birth-like year (<= current year - 15): employment years stay
FULL_DATE = re.compile(
    r"(?<!\d)(?:(\d{1,2})\s?[/\-.]\s?(\d{1,2})\s?[/\-.]\s?((?:19|20)\d{2})|((?:19|20)\d{2})\s?[/\-.]\s?(\d{1,2})\s?[/\-.]\s?(\d{1,2}))(?!\d)"
)
AGE_LINE = re.compile(
    rf"({kw('العمر', 'السن')}|age){SEP}(?P<val>\d{{1,2}})(?:\s*(?:سنة|عامًا|عاما|years?))?", re.I
)
AGE_PHRASE = re.compile(r"(?<!\d)(\d{2})\s*(?:years?\s+old|عامًا من العمر|سنة من العمر)", re.I)
NATIONALITY_LINE = re.compile(rf"({kw('الجنسية')}|nationality){SEP}(?P<val>[^\n،,|]{{2,30}})", re.I)
NATIONALITY_WORDS = [
    "السعودية",
    "السعودي",
    "سعودية",
    "سعودي",
    "سعوديين",
    "سعوديون",
    "مصر",
    "المصرية",
    "المصري",
    "مصرية",
    "مصري",
    "مصريين",
    "اليمن",
    "اليمنية",
    "اليمني",
    "يمنية",
    "يمني",
    "السودان",
    "السودانية",
    "السوداني",
    "سودانية",
    "سوداني",
    "باكستان",
    "الباكستانية",
    "الباكستاني",
    "باكستانية",
    "باكستاني",
    "الهند",
    "الهندية",
    "الهندي",
    "هندية",
    "هندي",
    "سوريا",
    "سورية",
    "السورية",
    "السوري",
    "سوري",
    "الأردن",
    "الاردن",
    "الأردنية",
    "الأردني",
    "أردنية",
    "أردني",
    "اردني",
    "فلسطين",
    "الفلسطينية",
    "الفلسطيني",
    "فلسطينية",
    "فلسطيني",
    "لبنان",
    "اللبنانية",
    "اللبناني",
    "لبنانية",
    "لبناني",
    "بنجلاديش",
    "بنغلاديش",
    "بنغالية",
    "بنغالي",
    "بنجالي",
    "الفلبين",
    "الفلبينية",
    "الفلبيني",
    "فلبينية",
    "فلبيني",
    "نيبال",
    "نيبالية",
    "نيبالي",
    "أفغانستان",
    "أفغانية",
    "أفغاني",
    "إثيوبيا",
    "إثيوبية",
    "إثيوبي",
    "Saudi Arabia",
    "Saudi",
    "Egypt",
    "Egyptian",
    "Yemen",
    "Yemeni",
    "Sudan",
    "Sudanese",
    "Pakistan",
    "Pakistani",
    "India",
    "Indian",
    "Syria",
    "Syrian",
    "Jordan",
    "Jordanian",
    "Palestine",
    "Palestinian",
    "Lebanon",
    "Lebanese",
    "Bangladesh",
    "Bangladeshi",
    "Philippines",
    "Filipino",
    "Filipina",
    "Nepal",
    "Nepali",
    "Nepalese",
    "Afghanistan",
    "Afghan",
    "Ethiopia",
    "Ethiopian",
    "KSA",
]
NATIONALITY = re.compile(
    B0
    + "(?:"
    + "|".join(sorted(map(re.escape, NATIONALITY_WORDS), key=len, reverse=True))
    + ")"
    + B1,
    re.I,
)
GENDER_LINE = re.compile(
    rf"({kw('الجنس', 'النوع')}|gender|sex){SEP}(?P<val>ذكر|أنثى|انثى|male|female)", re.I
)
GENDER_STANDALONE = re.compile(r"(?m)^\s*(?:ذكر|أنثى|انثى|male|female)\s*$", re.I)
GENDER_WORD = re.compile(B0 + r"(?:أنثى|انثى|male|female)" + B1, re.I)
ADDRESS_LINE = re.compile(
    rf"({kw('العنوان', 'السكن')}|عنوان\s+{kw('السكن')}|address){SEP}(?P<val>[^\n]{{3,120}})", re.I
)
ADDRESS_PARTS = re.compile(
    rf"{B0}(?:حي|شارع|طريق)\s+[؀-ۿ]+(?:\s+[؀-ۿ]+)?{B1}"
    r"|(?:ص\.?\s?ب\.?|P\.?\s?O\.?\s?Box)\s*[:：]?\s*\d+"
    r"|(?<!\d)\d{5}\s*[-–]\s*\d{4}(?!\d)",  # Saudi postal code - additional number
    re.I,
)
NAME_LINE = re.compile(
    rf"(?m)^(?:{kw('الاسم')}(?:\s+{kw('الكامل', 'الرباعي')})?|full\s+name|name){SEP}(?P<val>[^\n]{{2,80}})$",
    re.I,
)
ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
