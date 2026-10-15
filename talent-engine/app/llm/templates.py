"""Reusable profile templates (the fake provider's "draft"; also used by the seed)."""

from __future__ import annotations

from typing import Any

from app.llm.base import DraftCriteria

YEARS_RUBRIC = [
    {"level": 0, "text": "لا يوجد", "gte": None, "gt": None},
    {"level": 25, "text": "أقل من سنة", "gt": 0},
    {"level": 50, "text": "1–2 سنة", "gte": 1},
    {"level": 75, "text": "3–5 سنوات", "gt": 2},
    {"level": 100, "text": "أكثر من 5", "gt": 5},
]


def three_way(no: str, mid: str, yes: str) -> list[dict[str, Any]]:
    return [
        {"level": 0, "text": no, "answers": [no]},
        {"level": 25, "text": "—"},
        {"level": 50, "text": mid, "answers": [mid]},
        {"level": 75, "text": "—"},
        {"level": 100, "text": yes, "answers": [yes]},
    ]


GENERIC_RUBRIC = [
    {"level": 0, "text": "لا يوجد", "answers": ["لا يوجد"]},
    {"level": 25, "text": "أساسي", "answers": ["أساسي"]},
    {"level": 50, "text": "متوسط", "answers": ["متوسط"]},
    {"level": 75, "text": "جيد", "answers": ["جيد"]},
    {"level": 100, "text": "متقدم", "answers": ["متقدم"]},
]

LANG_RUBRIC = [
    {"level": 0, "text": "لا شيء"},
    {"level": 25, "text": "—"},
    {"level": 50, "text": "العربية فقط", "answers": ["العربية"]},
    {"level": 75, "text": "—"},
    {"level": 100, "text": "العربية والإنجليزية", "answers": ["العربية", "الإنجليزية"]},
]

SEC_QUESTIONS: list[dict[str, Any]] = [
    {
        "key": "edu",
        "label": "أعلى مؤهل دراسي",
        "label_en": "Highest qualification",
        "type": "select",
        "options": ["ثانوي", "دبلوم", "بكالوريوس", "أعلى"],
    },
    {
        "key": "years_sec",
        "label": "عدد سنوات الخبرة في المجال الأمني",
        "label_en": "Years of experience in security",
        "type": "number",
        "hint": "اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب",
    },
    {
        "key": "years_sup",
        "label": "عدد سنوات الخبرة في الإشراف على أفراد أمن",
        "label_en": "Years supervising security guards",
        "type": "number",
        "hint": "اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب",
    },
    {
        "key": "max_team",
        "label": "أكبر عدد من الأفراد أشرفت عليهم",
        "label_en": "Largest team you supervised",
        "type": "number",
    },
    {
        "key": "shifts",
        "label": "هل أعددت جداول مناوبة أو وزّعت ورديات؟",
        "label_en": "Did you prepare rosters or allocate shifts?",
        "type": "select",
        "options": ["لا", "شاركت", "أعددتها بنفسي"],
    },
    {
        "key": "licence",
        "label": "هل لديك رخصة حارس أمن؟",
        "label_en": "Do you hold a security guard licence?",
        "type": "select",
        "options": ["لا", "منتهية أو قيد الإصدار", "سارية"],
    },
    {
        "key": "licence_exp",
        "label": "تاريخ انتهاء الرخصة",
        "label_en": "Licence expiry date",
        "type": "date",
        "required": False,
    },
    {
        "key": "reports",
        "label": "هل تكتب تقارير أمنية أو تسجّل الحوادث؟",
        "label_en": "Do you write security reports or log incidents?",
        "type": "select",
        "options": ["لا", "أحيانًا", "بانتظام"],
    },
    {
        "key": "first_aid",
        "label": "دورة إسعافات أولية أو سلامة",
        "label_en": "First aid or safety course",
        "type": "select",
        "options": ["لا", "أقدم من سنتين", "حديثة"],
    },
    {
        "key": "languages",
        "label": "اللغات",
        "label_en": "Languages",
        "type": "multiselect",
        "options": ["العربية", "الإنجليزية", "أخرى"],
    },
    {
        "key": "last_job",
        "label": "صف آخر عمل في سطرين",
        "label_en": "Describe your last job in two lines",
        "type": "text",
        "required": False,
    },
]


def crit(
    key: str,
    text: str,
    text_en: str,
    weight: float,
    mandatory: bool,
    question: str | None,
    rubric: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "key": key,
        "text": text,
        "text_en": text_en,
        "weight": weight,
        "mandatory": mandatory,
        "question": question,
        "rubric": rubric,
    }


SEC_SUPERVISOR_CRITERIA: list[dict[str, Any]] = [
    crit(
        "supervision",
        "خبرة الإشراف على أفراد الأمن",
        "Experience supervising security guards",
        30,
        True,
        "years_sup",
        YEARS_RUBRIC,
    ),
    crit(
        "security_exp",
        "الخبرة الأمنية العامة",
        "General security experience",
        20,
        True,
        "years_sec",
        YEARS_RUBRIC,
    ),
    crit(
        "shifts",
        "إدارة الورديات وجداول المناوبة",
        "Shift and roster management",
        15,
        False,
        "shifts",
        three_way("لا", "شاركت", "أعددتها بنفسي"),
    ),
    crit(
        "licence",
        "رخصة حارس أمن",
        "Security guard licence",
        15,
        False,
        "licence",
        three_way("لا", "منتهية أو قيد الإصدار", "سارية"),
    ),
    crit(
        "reports",
        "كتابة التقارير الأمنية",
        "Writing security reports",
        8,
        False,
        "reports",
        three_way("لا", "أحيانًا", "بانتظام"),
    ),
    crit(
        "first_aid",
        "إسعافات أولية أو سلامة",
        "First aid or safety training",
        7,
        False,
        "first_aid",
        three_way("لا", "أقدم من سنتين", "حديثة"),
    ),
    crit("languages", "اللغات", "Languages", 5, False, "languages", LANG_RUBRIC),
]

SEC_SUPERVISOR_RULES: list[dict[str, Any]] = [
    {"fact": "nationality", "operator": "in", "value": ["السعودية"], "if_missing": "review"},
    {"fact": "height_cm", "operator": ">=", "value": 180, "if_missing": "review"},
    {"fact": "weight_kg", "operator": "<=", "value": 80, "if_missing": "review"},
    {"fact": "age", "operator": ">=", "value": 18, "if_missing": "review"},  # placeholder value
]

SEC_SUPERVISOR_DESCRIPTION = (
    "الإشراف اليومي على أفراد الأمن في الموقع، توزيع الورديات وإعداد جداول المناوبة، "
    "متابعة الالتزام بالإجراءات الأمنية، كتابة التقارير الأمنية وتقارير الحوادث، "
    "والتنسيق مع إدارة العمليات والجهات المختصة عند الحاجة."
)

GENERIC_QUESTIONS: list[dict[str, Any]] = [
    {
        "key": "years_exp",
        "label": "عدد سنوات الخبرة في المجال",
        "label_en": "Years of experience",
        "type": "number",
        "hint": "اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب",
    },
    {
        "key": "skill_main",
        "label": "مستواك في المهارة الأساسية للوظيفة",
        "label_en": "Your level in the main skill",
        "type": "select",
        "options": ["لا يوجد", "أساسي", "متوسط", "جيد", "متقدم"],
    },
    {
        "key": "languages",
        "label": "اللغات",
        "label_en": "Languages",
        "type": "multiselect",
        "options": ["العربية", "الإنجليزية", "أخرى"],
    },
]


def draft_for_title(title: str, description: str) -> DraftCriteria:
    t = title.lower()
    if any(w in t for w in ("أمن", "حراس", "security", "guard")):
        return DraftCriteria(
            description=description or SEC_SUPERVISOR_DESCRIPTION,
            criteria=SEC_SUPERVISOR_CRITERIA,
            questions=SEC_QUESTIONS,
            rules=SEC_SUPERVISOR_RULES,
        )
    return DraftCriteria(
        description=description or f"وصف مقترح لوظيفة {title} (مسودة، يعدّلها HR).",
        criteria=[
            crit(
                "experience",
                "سنوات الخبرة في المجال",
                "Years of experience",
                50,
                True,
                "years_exp",
                YEARS_RUBRIC,
            ),
            crit(
                "main_skill",
                "المهارة الأساسية للوظيفة",
                "Main skill for the role",
                30,
                False,
                "skill_main",
                GENERIC_RUBRIC,
            ),
            crit("languages", "اللغات", "Languages", 20, False, "languages", LANG_RUBRIC),
        ],
        questions=GENERIC_QUESTIONS,
        rules=[],
    )
