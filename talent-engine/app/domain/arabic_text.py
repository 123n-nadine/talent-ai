"""Short Arabic UI phrases with correct number agreement (stage notes, counts).

Arabic counts: 1 → «صفحة واحدة», 2 → «صفحتان», 3–10 → plural, 11+ → singular, 0 → «لا …»."""

from __future__ import annotations

REDACTION_LABELS = {
    "name": "الاسم",
    "phone": "الهاتف",
    "email": "البريد",
    "national_id": "رقم الهوية",
    "dob": "تاريخ الميلاد",
    "age": "العمر",
    "nationality": "الجنسية",
    "gender": "الجنس",
    "address": "العنوان",
    "url": "رابط",
}


def count(n: int | float, one: str, two: str, plural: str, feminine: bool = False) -> str:
    """«3 صفحات», «صفحة واحدة», «صفحتان», «11 صفحة», «لا صفحة»."""
    n = int(n)
    if n == 0:
        return f"لا {one}"
    if n == 1:
        return f"{one} {'واحدة' if feminine else 'واحد'}"
    if n == 2:
        return two
    if 3 <= n <= 10:
        return f"{n} {plural}"
    return f"{n} {one}"


def extraction_label(method: str | None) -> str:
    m = method or ""
    base = m.split("+")[-1]
    if base.startswith("ocr:"):
        label = "قراءة ضوئية (OCR)"
    elif base == "pdf_text":
        label = "نص PDF مباشر"
    elif base == "docx":
        label = "ملف Word"
    else:
        label = base or "—"
    if m.startswith("libreoffice+"):
        label = "ملف DOC/RTF محوَّل إلى PDF"
    return label


REDACTION_LABELS_EN = {
    "name": "name",
    "phone": "phone",
    "email": "e-mail",
    "national_id": "ID number",
    "dob": "date of birth",
    "age": "age",
    "nationality": "nationality",
    "gender": "gender",
    "address": "address",
    "url": "link",
}


def count_en(n: int | float, one: str, many: str) -> str:
    n = int(n)
    return f"{n} {one if n == 1 else many}"


def extraction_label_en(method: str | None) -> str:
    m = method or ""
    base = m.split("+")[-1]
    if m.startswith("libreoffice+"):
        return "DOC/RTF converted to PDF"
    if base.startswith("ocr:"):
        return "OCR (scanned image)"
    return {"pdf_text": "PDF text layer", "docx": "Word file"}.get(base, base or "—")


def redaction_note_en(counts: dict[str, int]) -> str:
    if not counts:
        return "no personal data found"
    total = sum(int(v) for v in counts.values())
    parts = ", ".join(f"{REDACTION_LABELS_EN.get(k, k)} ({v})" for k, v in counts.items())
    return f"{count_en(total, 'item', 'items')} hidden: {parts}"


def redaction_note(counts: dict[str, int]) -> str:
    if not counts:
        return "لم يُعثر على بيانات شخصية"
    total = sum(int(v) for v in counts.values())
    parts = "، ".join(f"{REDACTION_LABELS.get(k, k)} ({v})" for k, v in counts.items())
    return f"أُخفي {count(total, 'بيان', 'بيانان', 'بيانات')}: {parts}"
