"""Chapter 8: the score — formula, worked example with the real numbers, coverage and bands, why
it is not a probability."""

from __future__ import annotations

from inv import line
from model import Bullets, Chapter, Field, Img, Note, P, Page, Table, Tech


def score(F: dict) -> Chapter:
    ex = F["example"]
    rows, total, covered, wsum = [], 0.0, 0.0, 0.0
    for c in ex["criteria"]:
        w = float(c.get("weight") or 0)
        lvl = float(c.get("level") or 0)
        part = w * lvl / 100
        total += part
        wsum += w
        if c.get("source") != "missing" and (c.get("evidence") or c.get("cv_quote")):
            covered += w
        rows.append([c.get("text") or c["key"], f"{w:g}%", f"{lvl:g}", f"{part:g}"])
    rows.append(["المجموع", f"{wsum:g}%", "", f"{total:g}"])
    assert abs(total - float(ex["score"])) < 0.05, (total, ex["score"])  # the guide never shows a number the system did not compute
    cov = round(ex["coverage"] * 100)
    band_ar = {"high": "مرتفعة", "medium": "متوسطة", "low": "منخفضة"}[ex["band"]]
    pages = [
        Page("score-formula", "المعادلة", [
            Img("images/steps/S10d_how.png", "مربع «كيف يُحسب» في صفحة الترتيب.", 0.6, 9),
            P("كل معيار ليه وزن، والأوزان مجموعها 100%.\n"
              "وكمان المعيار بياخد مستوى من خمسة بس: 0 أو 25 أو 50 أو 75 أو 100.\n"
              "الدرجة هي مجموع الوزن مضروب في المستوى، مقسوم على 100."),
            P("يعني معيار وزنه 30% والمستوى بتاعه 75 بيدّي 22.5 نقطة.\n"
              "مفيش أي رقم بيحسبه النموذج اللغوي: الحساب كله في الكود."),
            Tech([line("decision:claude:2")]),
        ], terms=["المعادلة", "الوزن", "المستوى"]),
        Page("score-example", f"مثال بالأرقام: {ex['name']}", [
            P(f"ده الحساب الحقيقي لـ {ex['name']} من الديمو، صف صف."),
            Table(["المعيار", "الوزن", "المستوى", "النقط"], rows, widths=(0.52, 0.16, 0.16, 0.16)),
            P(f"المجموع {total:g} من 100، وده نفس الرقم اللي في شاشته بالظبط.\n"
              f"ترتيبه {ex.get('rank', '—')} من {ex.get('ranked_total', '—')} في الشاغر."),
        ], terms=["النقط"]),
        Page("score-coverage", "التغطية والفئات", [
            Field("التغطية", "مجموع أوزان المعايير اللي ليها دليل، مقسوم على مجموع الأوزان كلها."),
            Field(f"عند {ex['name']}", f"التغطية {cov}%، والفئة {band_ar}."),
            Bullets(["مرتفعة: 75 أو أكتر.", "متوسطة: من 50 لحد 74.9.", "منخفضة: أقل من 50.",
                     "معيار إلزامي في المستوى صفر: الفئة منخفضة مهما كانت الدرجة.",
                     "معيار إلزامي من غير دليل: الطلب يحتاج مراجعة.",
                     "تغطية أقل من 60%: الطلب يحتاج مراجعة."]),
            Note("الألوان ثابتة في كل الشاشات: الأخضر مرتفعة، والأصفر متوسطة، والأحمر منخفضة.", "info"),
        ], terms=["التغطية", "الفئة"]),
        Page("score-not-probability", "ليه الدرجة مش احتمال نجاح", [
            P("الدرجة بتقول المتقدم قريب قد إيه من المعايير اللي الموارد البشرية كتبتها.\n"
              "مش بتقول هينجح في الشغل ولا لأ.\n"
              "لو المعايير اتغيرت، الدرجة بتتغير معاها."),
            P("عشان كده الجملة دي مكتوبة جنب كل درجة في كل الشاشات:\n"
              "الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة."),
            Note("الدرجة بتساعد ترتّبي، والقرار بتاخديه إنتي بعد ما تشوفي الأدلة.", "warn"),
        ], terms=["احتمال النجاح"]),
    ]
    return Chapter("score", "8 — الدرجة", pages)
