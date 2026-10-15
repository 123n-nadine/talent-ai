"""Build the gold set: 50 synthetic applicants (35 "مشرف أمن", 15 "محلل بيانات") with expected
eligibility, expected level per criterion and expected flags. Deterministic (seeded), fictional.

Outputs: eval/gold/security_supervisor.json, eval/gold/data_analyst.json (machine-readable) and
eval/gold/GOLD_SET.md (for Nadine's review). Usage: uv run python -m eval.make_gold
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.templates import (  # noqa: E402
    GENERIC_RUBRIC,
    SEC_QUESTIONS,
    SEC_SUPERVISOR_CRITERIA,
    SEC_SUPERVISOR_DESCRIPTION,
    SEC_SUPERVISOR_RULES,
    YEARS_RUBRIC,
    crit,
)
from app.pipeline.stages.answers import normalise_one  # noqa: E402
from app.scoring.rubric import level_from_rubric  # noqa: E402

OUT = Path(__file__).resolve().parent / "gold"
rng = random.Random(2026)

# ---------------------------------------------------------------- jobs
ANALYST_QUESTIONS = [
    {
        "key": "years_exp",
        "label": "عدد سنوات الخبرة في تحليل البيانات",
        "type": "number",
        "hint": "اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب",
    },
    {
        "key": "sql",
        "label": "مستواك في SQL",
        "type": "select",
        "options": ["لا يوجد", "أساسي", "متوسط", "جيد", "متقدم"],
    },
    {
        "key": "python",
        "label": "مستواك في Python",
        "type": "select",
        "options": ["لا يوجد", "أساسي", "متوسط", "جيد", "متقدم"],
    },
    {
        "key": "project",
        "label": "صف مشروع تحليل بيانات نفّذته (ما المشكلة، ما الأدوات، ما النتيجة)",
        "type": "text",
        "required": False,
    },
]
PROJECT_RUBRIC = [
    {"level": 0, "text": "لا يوجد وصف أو وصف لا علاقة له بتحليل البيانات"},
    {"level": 25, "text": "ذكر عام بدون مشكلة أو أدوات أو نتيجة"},
    {"level": 50, "text": "مشكلة وأداة واحدة على الأقل، بدون نتيجة واضحة"},
    {"level": 75, "text": "مشكلة وأدوات ونتيجة، لكن بدون أثر أو أرقام"},
    {"level": 100, "text": "مشكلة وأدوات ونتيجة بأثر ملموس أو أرقام"},
]
ANALYST_CRITERIA = [
    crit(
        "experience",
        "سنوات الخبرة في تحليل البيانات",
        "Years of analytics experience",
        30,
        True,
        "years_exp",
        YEARS_RUBRIC,
    ),
    crit(
        "sql", "SQL واستخراج البيانات", "SQL and data extraction", 30, True, "sql", GENERIC_RUBRIC
    ),
    crit(
        "python",
        "Python لتحليل البيانات",
        "Python for data analysis",
        20,
        False,
        "python",
        GENERIC_RUBRIC,
    ),
    crit(
        "project",
        "وصف مشروع تحليلي (إجابة حرة يحكم عليها النموذج)",
        "Analytics project description",
        20,
        False,
        "project",
        PROJECT_RUBRIC,
    ),
]
JOBS = {
    "GOLD-SEC": {
        "title": "مشرف أمن — مجموعة الاختبار",
        "description": SEC_SUPERVISOR_DESCRIPTION,
        "criteria": SEC_SUPERVISOR_CRITERIA,
        "rules": SEC_SUPERVISOR_RULES,
        "questions": SEC_QUESTIONS,
        "approved_by": "gold-set",
    },
    "GOLD-ANALYST": {
        "title": "محلل بيانات — مجموعة الاختبار",
        "description": "تحليل بيانات العمليات وبناء لوحات المعلومات.",
        "criteria": ANALYST_CRITERIA,
        "rules": [],
        "questions": ANALYST_QUESTIONS,
        "approved_by": "gold-set",
    },
}

SEL3 = {
    "shifts": ["لا", "شاركت", "أعددتها بنفسي"],
    "licence": ["لا", "منتهية أو قيد الإصدار", "سارية"],
    "reports": ["لا", "أحيانًا", "بانتظام"],
    "first_aid": ["لا", "أقدم من سنتين", "حديثة"],
}
LANG = [["العربية"], ["العربية", "الإنجليزية"], ["الإنجليزية"]]
FIRST = [
    "عبدالله",
    "محمد",
    "خالد",
    "سعود",
    "فهد",
    "تركي",
    "نواف",
    "بدر",
    "ماجد",
    "سلمان",
    "ياسر",
    "عمر",
    "راكان",
    "مشاري",
    "وليد",
]
LAST = [
    "الغامدي",
    "القحطاني",
    "العتيبي",
    "الشمري",
    "الدوسري",
    "المطيري",
    "الزهراني",
    "الحربي",
    "السبيعي",
    "البقمي",
    "العنزي",
    "الجهني",
]


def years_level(y: float) -> int:
    return level_from_rubric(YEARS_RUBRIC, "number", normalise_one("y", "number", y))


def sel_level(key: str, v: str) -> int:
    return [0, 50, 100][SEL3[key].index(v)]


def lang_level(v: list[str]) -> int:
    return 100 if "العربية" in v and "الإنجليزية" in v else 50 if "العربية" in v else 0


def gen_sec(i: int, archetype: str) -> dict:
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    facts = {
        "nationality": "السعودية",
        "height_cm": rng.randint(180, 190),
        "weight_kg": rng.randint(65, 80),
        "age": rng.randint(22, 45),
    }
    ans: dict = {"edu": rng.choice(["ثانوي", "دبلوم", "بكالوريوس"])}
    exp: dict = {}
    flags: list[str] = []
    elig = "eligible"
    if archetype == "strong":
        ans.update(
            years_sec=rng.randint(6, 14),
            years_sup=rng.randint(6, 10),
            shifts="أعددتها بنفسي",
            licence="سارية",
            reports="بانتظام",
            first_aid=rng.choice(["حديثة", "أقدم من سنتين"]),
            languages=["العربية", "الإنجليزية"],
        )
    elif archetype == "medium":
        ans.update(
            years_sec=rng.randint(3, 6),
            years_sup=rng.choice([1, 2, 3, 4, 5]),
            shifts=rng.choice(["شاركت", "أعددتها بنفسي"]),
            licence=rng.choice(["سارية", "منتهية أو قيد الإصدار"]),
            reports=rng.choice(["أحيانًا", "بانتظام"]),
            first_aid=rng.choice(["لا", "أقدم من سنتين"]),
            languages=rng.choice([["العربية"], ["العربية", "الإنجليزية"]]),
        )
    elif archetype == "low":
        ans.update(
            years_sec=rng.choice([0, 0.5, 1, 2]),
            years_sup=rng.choice([0, 0, 0.5]),
            shifts="لا",
            licence=rng.choice(["لا", "منتهية أو قيد الإصدار"]),
            reports="لا",
            first_aid="لا",
            languages=rng.choice(LANG),
        )
    elif archetype == "not_eligible":
        ans.update(
            years_sec=rng.randint(4, 10),
            years_sup=rng.randint(2, 7),
            shifts="أعددتها بنفسي",
            licence="سارية",
            reports="بانتظام",
            first_aid="حديثة",
            languages=["العربية", "الإنجليزية"],
        )
        which = rng.choice(["height", "weight", "nationality"])
        if which == "height":
            facts["height_cm"] = rng.randint(165, 179)
        elif which == "weight":
            facts["weight_kg"] = rng.randint(82, 95)
        else:
            facts["nationality"] = rng.choice(["مصر", "اليمن", "السودان"])
        elig = "not_eligible"
    elif archetype == "needs_review_fact":
        ans.update(
            years_sec=rng.randint(3, 9),
            years_sup=rng.randint(1, 6),
            shifts="شاركت",
            licence="سارية",
            reports="أحيانًا",
            first_aid="لا",
            languages=["العربية"],
        )
        facts[rng.choice(["height_cm", "weight_kg"])] = None
        elig = "needs_review"
    elif archetype == "blank_heavy":
        ans.update(
            years_sec=rng.randint(2, 8),
            years_sup="",
            shifts="",
            licence="",
            reports="",
            first_aid="",
            languages=["العربية"],
        )
        flags += ["low_coverage", "mandatory_missing", "missing_evidence"]
    elif archetype == "contradiction":
        ans.update(
            years_sec=rng.randint(6, 10),
            years_sup=rng.choice([6, 7, 8]),
            shifts="أعددتها بنفسي",
            licence="سارية",
            reports="بانتظام",
            first_aid="حديثة",
            languages=["العربية", "الإنجليزية"],
        )
        flags += ["contradiction"]
    # expected levels from the rubric (structured answers)
    for key, qk in (("supervision", "years_sup"), ("security_exp", "years_sec")):
        v = ans[qk]
        exp[key] = None if v == "" else years_level(float(v))
    for key in ("shifts", "licence", "reports", "first_aid"):
        exp[key] = None if ans[key] == "" else sel_level(key, ans[key])
    exp["languages"] = lang_level(ans["languages"])
    # CV text (Arabic) for most applicants; contradiction: the CV states fewer supervision years
    cv = None
    cv_years_sup = None
    if archetype != "blank_heavy" and rng.random() < 0.75:
        ys = ans["years_sec"]
        sup = ans["years_sup"] if ans["years_sup"] != "" else 0
        if archetype == "contradiction":
            cv_years_sup = 2
            exp["supervision"] = years_level(2)  # the lower, CV-backed level is used
        start = 2026 - int(float(ys)) if float(ys) else None
        lines = [
            f"{name} — {'مشرف أمن' if sup else 'حارس أمن'}",
            "الاسم: " + name,
            f"الجوال: 05{rng.randint(10000000, 99999999)}",
            f"الجنسية: {facts['nationality']}",
            f"العمر: {facts['age']}",
        ]
        if start:
            lines.append(
                f"أعمل في مجال الأمن والحراسة منذ {start}، أي خبرة {int(float(ys))} سنوات."
            )
        if cv_years_sup is not None:
            lines.append(
                f"عملت مشرف وردية لمدة سنتين فقط (من {2026 - 2} حتى الآن) على فريق من {rng.randint(4, 9)} أفراد."
            )
        elif sup:
            lines.append(
                f"أشرف على فريق من {rng.randint(5, 25)} فردًا منذ {2026 - int(float(sup))} حتى الآن."
            )
        if ans["shifts"] == "أعددتها بنفسي":
            lines.append("أتولى إعداد جداول المناوبة وتوزيع الورديات بنفسي.")
        elif ans["shifts"] == "شاركت":
            lines.append("شاركت في إعداد جداول المناوبة مع المشرف.")
        if ans["licence"] == "سارية":
            lines.append("حاصل على رخصة حارس أمن سارية حتى 2028.")
        elif ans["licence"] == "منتهية أو قيد الإصدار":
            lines.append("رخصة حارس الأمن منتهية وقيد التجديد.")
        if ans["reports"] == "بانتظام":
            lines.append("أكتب التقارير الأمنية اليومية وتقارير الحوادث بانتظام.")
        elif ans["reports"] == "أحيانًا":
            lines.append("أكتب تقارير الحوادث عند الحاجة.")
        if ans["first_aid"] == "حديثة":
            lines.append("حاصل على دورة إسعافات أولية حديثة من الهلال الأحمر (2025).")
        elif ans["first_aid"] == "أقدم من سنتين":
            lines.append("حاصل على دورة إسعافات أولية عام 2021.")
        lines.append(
            "اللغة العربية لغة أم"
            + ("، وإجادة الإنجليزية بمستوى جيد." if "الإنجليزية" in ans["languages"] else ".")
        )
        cv = lines
    return {
        "ref": f"GOLD-SEC-{i:03d}",
        "job": "GOLD-SEC",
        "archetype": archetype,
        "name_hint": name,
        "facts": facts,
        "answers": ans,
        "cv_lines": cv,
        "expected": {"eligibility": elig, "levels": exp, "flags": flags},
    }


PROJECTS = {
    100: (
        "حللت بيانات شكاوى العملاء (40 ألف سجل) بـ SQL وPython لمعرفة أسباب التأخير، وبنيت لوحة في Power BI؛ انخفض زمن الاستجابة 30% خلال ثلاثة أشهر.",
        100,
    ),
    75: (
        "جمعت بيانات المبيعات من ثلاثة فروع بـ SQL ونظفتها بـ pandas وأعددت تقريرًا شهريًا للإدارة بأهم المنتجات.",
        75,
    ),
    50: ("استخدمت Excel وSQL لتحليل بيانات الحضور ومعرفة أيام الغياب المتكررة.", 50),
    25: ("عملت على تحليل البيانات في وظيفتي السابقة.", 25),
    0: ("أحب العمل الجماعي وأتعلم بسرعة.", 0),
}


def gen_analyst(i: int, archetype: str) -> dict:
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    facts = {"nationality": rng.choice(["السعودية", "السعودية", "مصر"]), "age": rng.randint(22, 40)}
    lv = {
        "strong": (rng.randint(6, 10), "متقدم", rng.choice(["جيد", "متقدم"]), 100),
        "medium": (
            rng.choice([2, 3, 4]),
            rng.choice(["متوسط", "جيد"]),
            rng.choice(["أساسي", "متوسط"]),
            rng.choice([50, 75]),
        ),
        "low": (
            rng.choice([0, 0.5, 1]),
            rng.choice(["لا يوجد", "أساسي"]),
            "لا يوجد",
            rng.choice([0, 25]),
        ),
        "no_project": (rng.choice([2, 5]), "جيد", "متوسط", None),
    }[archetype]
    years, sql, py, plevel = lv
    ans = {
        "years_exp": years,
        "sql": sql,
        "python": py,
        "project": PROJECTS[plevel][0] if plevel is not None else "",
    }
    exp = {
        "experience": years_level(years),
        "sql": GENERIC_RUBRIC[["لا يوجد", "أساسي", "متوسط", "جيد", "متقدم"].index(sql)]["level"],
        "python": GENERIC_RUBRIC[["لا يوجد", "أساسي", "متوسط", "جيد", "متقدم"].index(py)]["level"],
        "project": plevel,
    }
    flags = ["missing_evidence"] if plevel is None else []
    return {
        "ref": f"GOLD-ANA-{i:03d}",
        "job": "GOLD-ANALYST",
        "archetype": archetype,
        "name_hint": name,
        "facts": facts,
        "answers": ans,
        "cv_lines": None,
        "expected": {
            "eligibility": "eligible",
            "levels": exp,
            "flags": flags,
            "project_tolerance": 25,
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sec_plan = (
        ["strong"] * 8
        + ["medium"] * 10
        + ["low"] * 5
        + ["not_eligible"] * 4
        + ["needs_review_fact"] * 3
        + ["blank_heavy"] * 2
        + ["contradiction"] * 3
    )
    ana_plan = ["strong"] * 4 + ["medium"] * 5 + ["low"] * 4 + ["no_project"] * 2
    sec = [gen_sec(i + 1, a) for i, a in enumerate(sec_plan)]
    ana = [gen_analyst(i + 1, a) for i, a in enumerate(ana_plan)]
    (OUT / "security_supervisor.json").write_text(
        json.dumps({"job": JOBS["GOLD-SEC"], "applicants": sec}, ensure_ascii=False, indent=2)
    )
    (OUT / "data_analyst.json").write_text(
        json.dumps({"job": JOBS["GOLD-ANALYST"], "applicants": ana}, ensure_ascii=False, indent=2)
    )
    # review document
    md = [
        "# مجموعة الاختبار (Gold set) — للمراجعة",
        "",
        "50 متقدمًا صناعيًا (أسماء وهمية). لكل متقدم: الإجابات، الحقائق، هل له سيرة ذاتية، والمستوى **المتوقع** لكل معيار حسب جدول المستويات المعتمد.",
        "القواعد: الفراغ = لم يُجب (دليل ناقص)، 0 = إجابة حقيقية. الأهلية تُحسب من الحقائق. في حالات «تعارض» السيرة تقول سنتين إشراف فقط فيُستخدم المستوى الأدنى ويُطلب مراجعة.",
        "",
        "## مشرف أمن (35 متقدمًا)",
        "",
        "| المرجع | النوع | الحقائق | سنوات أمن | سنوات إشراف | ورديات | رخصة | تقارير | إسعافات | لغات | سيرة | الأهلية المتوقعة | المستويات المتوقعة (إشراف/أمن/ورديات/رخصة/تقارير/إسعافات/لغات) | علامات متوقعة |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for a in sec:
        f, an, e = a["facts"], a["answers"], a["expected"]
        lv = e["levels"]
        row = [
            a["ref"],
            a["archetype"],
            f"{f['nationality']}، {f['height_cm']} سم، {f['weight_kg']} كجم، {f['age']} سنة",
            str(an["years_sec"]),
            str(an["years_sup"]) if an["years_sup"] != "" else "—",
            an["shifts"] or "—",
            an["licence"] or "—",
            an["reports"] or "—",
            an["first_aid"] or "—",
            "، ".join(an["languages"]),
            "نعم" if a["cv_lines"] else "لا",
            e["eligibility"],
            "/".join(
                "—" if lv[k] is None else str(lv[k])
                for k in (
                    "supervision",
                    "security_exp",
                    "shifts",
                    "licence",
                    "reports",
                    "first_aid",
                    "languages",
                )
            ),
            "، ".join(e["flags"]) or "—",
        ]
        md.append("| " + " | ".join(row) + " |")
    md += [
        "",
        "## محلل بيانات (15 متقدمًا)",
        "",
        "| المرجع | النوع | سنوات | SQL | Python | وصف المشروع (إجابة حرة) | المستويات المتوقعة (خبرة/SQL/Python/مشروع) |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in ana:
        an, lv = a["answers"], a["expected"]["levels"]
        md.append(
            "| "
            + " | ".join(
                [
                    a["ref"],
                    a["archetype"],
                    str(an["years_exp"]),
                    an["sql"],
                    an["python"],
                    (an["project"] or "—")[:70],
                    "/".join(
                        "—" if lv[k] is None else str(lv[k])
                        for k in ("experience", "sql", "python", "project")
                    ),
                ]
            )
            + " |"
        )
    md += [
        "",
        "ملاحظة: معيار «وصف المشروع» هو الوحيد الذي يحكم عليه النموذج اللغوي من إجابة حرة؛ يُقبل فرق مستوى واحد (±25) فيه عند القياس.",
    ]
    (OUT / "GOLD_SET.md").write_text("\n".join(md) + "\n")
    print(f"gold set: {len(sec)} supervisor + {len(ana)} analyst applicants -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
