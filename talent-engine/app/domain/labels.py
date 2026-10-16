"""Arabic-first labels used in API output (the UI never shows raw codes)."""

STAGES: list[tuple[str, str, str]] = [
    ("intake", "استلام", "Intake"),
    ("answers", "قراءة إجابات النموذج", "Read form answers"),
    ("cv_text", "استخراج نص السيرة", "Extract CV text"),
    ("redaction", "إخفاء الهوية", "Redaction"),
    ("profile", "الملف المنظّم", "Structured profile"),
    ("evidence_check", "التحقق من الأدلة", "Evidence check"),
    ("eligibility", "الشروط الإلزامية", "Hard eligibility rules"),
    ("judgement", "الحكم على المعايير", "Criteria judgement"),
    ("scoring", "الدرجة والترتيب", "Score and rank"),
    ("index", "الفهرسة", "Index"),
]

NO_CV_NOTE = "لا توجد سيرة — التقييم من الإجابات فقط"
NO_CV_NOTE_EN = "No CV — assessed from the answers only"

AI_STATUS = {
    "queued": "Processing",
    "processing": "Processing",
    "completed": "Completed",
    "needs_review": "Needs Review",
    "failed": "Failed",
}

BANDS = {"high": ("مرتفعة", "High"), "medium": ("متوسطة", "Medium"), "low": ("منخفضة", "Low")}

ELIGIBILITY = {
    "eligible": ("مستوفٍ", "Eligible"),
    "not_eligible": ("غير مستوفٍ بحسب ما كتبه", "Not eligible (as declared)"),
    "needs_review": ("يحتاج مراجعة", "Needs review"),
}

FLAGS = {
    "missing_evidence": ("دليل ناقص", "Missing evidence"),
    "mandatory_missing": ("معيار إلزامي بلا دليل", "Mandatory criterion without evidence"),
    "mandatory_zero": ("معيار إلزامي عند المستوى 0", "Mandatory criterion at level 0"),
    "low_coverage": ("تغطية منخفضة", "Low coverage"),
    "contradiction": ("تعارض بين الإجابة والسيرة", "Answer contradicts the CV"),
    "evidence_mismatch": (
        "دليل لا يطابق الإجابة المخزّنة",
        "Evidence does not match the stored answer",
    ),
    "cv_unreadable": ("ملف السيرة غير مقروء", "CV file unreadable"),
    "low_ocr_confidence": ("ثقة OCR منخفضة", "Low OCR confidence"),
    "duplicate": ("طلب مكرر", "Duplicate application"),
    "stale": ("قديم — نسخة معايير سابقة", "Stale — previous criteria version"),
    "data_changed": ("النتيجة لا تعكس آخر تعديل", "Result does not reflect the latest edit"),
    "hr_override": ("تعديل HR", "HR override"),
}

GROUP_REASONS = {
    "duplicate": (
        "طلب مكرر — يُرتَّب الطلب الأصلي فقط",
        "Duplicate — only the original application is ranked",
    ),
    "processing": ("جاري المعالجة", "Processing"),
    "failed": ("فشلت المعالجة", "Processing failed"),
    "stale": ("قديم — نسخة معايير سابقة", "Stale — previous criteria version"),
    "data_changed": ("النتيجة لا تعكس آخر تعديل", "Result does not reflect the latest edit"),
    "not_eligible": ("غير مستوفٍ بحسب ما كتبه", "Not eligible (as declared)"),
    "needs_review": (
        "قيمة مفقودة أو تغطية منخفضة أو تعارض",
        "Missing value, low coverage or contradiction",
    ),
    "consent_withdrawn": (
        "مستبعد: سحب الموافقة — حُذفت بيانات الذكاء الاصطناعي الخاصة به",
        "Excluded: consent withdrawn — the AI data was erased",
    ),
}

SCORE_DISCLAIMER = "الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة."
