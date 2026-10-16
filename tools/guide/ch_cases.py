"""Chapter 9: special cases, one page each."""

from __future__ import annotations

from inv import line
from model import Chapter, Field, Img, Page, Tech


def _crit(case: dict, key: str) -> dict:
    return next((c for c in case.get("criteria", []) if c["key"] == key), {})


def cases(F: dict) -> Chapter:
    C = F["cases"]
    tt = F["tests"]["items"]
    ne, nr, blank, zero, contra, dup, corrupt = (C["not_eligible"], C["needs_review"], C["blank"], C["zero"], C["contradiction"], C["duplicate"], C["corrupt"])
    k07, k15, k02, k03b = tt.get("K07", {}), tt.get("K15", {}), tt.get("K02", {}), tt.get("K03b", {})
    failed = [c["text"] for c in ne.get("checks", []) if c.get("ok") is False]
    bsup, zsup = _crit(blank, "supervision"), _crit(zero, "supervision")
    cc = next((c for c in contra.get("criteria", []) if c.get("contradiction")), {})
    pages = [
        Page("case-not-eligible", "حالة 1 — غير مستوفٍ", [
            Img("images/steps/X_not_eligible.png", f"خلاصة تقييم {ne['name']}: الطول أقل من المطلوب.", 1.0, 11),
            Field("إيه اللي حصل", f"{ne['name']} كتب طوله، والرقم أقل من شرط الشاغر."),
            Field("الشرط اللي فشل", "، ".join(failed) or "—"),
            Field("النتيجة", "«غير مستوفٍ بحسب ما كتبه»، والدرجة رمادي، وبرّه الترتيب، بس الطلب محفوظ وموجود في بنك المتقدمين."),
            Field("في الاختبار", "متقدم مصري طوله 172 طلع بسببين مكتوبين، في الاختبار K02" if k02.get("ok") else "—"),
            Field("ليه «بحسب ما كتبه»", "النظام بيحكم على اللي المتقدم صرّح بيه، والموارد البشرية بتتأكد في المقابلة."),
        ], terms=["غير مستوفٍ"]),
        Page("case-needs-review", "حالة 2 — يحتاج مراجعة", [
            Img("images/steps/X_needs_review.png", f"خلاصة تقييم {nr['name']}: معيار إلزامي من غير إجابة.", 1.0, 11),
            Field("إيه اللي حصل", f"{nr['name']} ساب سؤال الإشراف فاضي، والإشراف معيار إلزامي، ومعندوش سيرة."),
            Field("النتيجة", "«يحتاج مراجعة»: النظام مش بيخمّن، وبيطلب من الموارد البشرية تبص بنفسها."),
            Field("وكمان", "طول فاضي من نظام بيسمح بكده بيدّي نفس النتيجة، زي اختبار الكونسول K03b" if k03b.get("ok") else "قيمة ناقصة في شرط إلزامي بتدّي نفس النتيجة."),
            Field("الفرق عن غير مستوفٍ", "غير مستوفٍ معناه القيمة موجودة وغلط؛ يحتاج مراجعة معناه القيمة ناقصة."),
        ], terms=["يحتاج مراجعة"]),
        Page("case-blank", "حالة 3 أ — الإجابة الفاضية", [
            Img("images/steps/X_blank.png", f"معيار الإشراف عند {blank['name']}: «دليل ناقص».", 1.0, 11),
            Field("إيه اللي حصل", f"سؤال سنين الإشراف فاضي، فالمستوى {bsup.get('level', 0)} ومعاه وسم «دليل ناقص»."),
            Field("ليه", "الفراغ معناه المتقدم ما جاوبش، والنظام عمره ما بيخمّن إجابة."),
            Field("لو عنده سيرة", f"الدليل ممكن ييجي من جملة في السيرة بتثبت الإشراف؛ ده اللي حصل مع {C['blank_with_cv']['name']}."),
        ], terms=["دليل ناقص", "الفراغ"]),
        Page("case-zero", "حالة 3 ب — الإجابة صفر", [
            Img("images/steps/X_zero.png", f"معيار الإشراف عند {zero['name']}: الإجابة صفر.", 1.0, 11),
            Field("إيه اللي حصل", f"المتقدم كتب صفر سنين، فالمستوى {zsup.get('level', 0)} والدليل «{zsup.get('evidence') or '0'}»."),
            Field("الفرق", "صفر إجابة حقيقية: المعيار متغطّي والتغطية مش بتقل، بعكس الفراغ."),
            Field("في الاختبار", "مقارنة الحالتين لقت الفرق ده بالظبط، في الاختبار K04" if tt.get("K04", {}).get("ok") else "—"),
        ], terms=["الصفر"]),
        Page("case-contradiction", "حالة 4 — الإجابة عكس السيرة", [
            Img("images/steps/X_contradiction_evidence.png", f"جدول الأدلة عند {contra['name']}: تعارض في معيار الإشراف.", 1.0, 11),
            Field("إيه اللي حصل", f"النموذج قال مستوى {cc.get('form_level', '—')}، والسيرة قالت {cc.get('cv_level', '—')}."),
            Field("الاقتباس", f"«{cc.get('cv_quote') or cc.get('evidence') or '—'}»"),
            Field("النتيجة", f"النظام خد المستوى الأقل ({cc.get('level', '—')})، وعلّم «تعارض»، والطلب يحتاج مراجعة."),
            Field("ليه الأقل", "عشان محدش يكسب نقط من إجابة السيرة مش بتأكدها."),
        ], terms=["التعارض"]),
        Page("case-duplicate", "حالة 5 — طلب مكرر", [
            Img("images/steps/X_duplicate.png", f"طلب {dup['name']} مربوط بطلب أقدم لنفس الشخص.", 1.0, 11),
            Field("إيه اللي حصل", "نفس رقم الهوية اتقدّم مرتين بإيميلين مختلفين."),
            Field("إزاي اتعرف", "بصمة رقم الهوية واحدة، من غير ما الرقم نفسه يوصل للمحرك."),
            Field("النتيجة", f"الطلب الجديد مربوط بالأصلي «{dup.get('duplicate_of_name') or '—'}»، ورمادي، والأصلي بس اللي بيترتّب."),
            Field("مفيش مسح", "النظام عمره ما بيمسح طلب لوحده؛ القرار للموارد البشرية."),
        ], terms=["الطلب المكرر"]),
        Page("case-corrupt", "حالة 6 — ملف سيرة تالف", [
            Img("images/steps/X_corrupt.png", f"خلاصة تقييم {corrupt['name']} وملاحظة الملف التالف.", 1.0, 11),
            Field("إيه اللي حصل", "الملف المرفوع تالف، فالنظام رفض يحفظه."),
            Field("الملاحظة اللي ظهرت", "الملف تالف أو غير آمن ومتحفظش، والتقييم من الإجابات بس."),
            Field("النتيجة", f"الطلب اتحفظ واتقيّم من الإجابات بس، ودرجته {corrupt.get('score', '—')}."),
            Field("وكمان", "ملف سيرة من النوع القديم كان بيوقّف التقييم، واتصلّح في الاختبار الشامل، ورقم الخطأ F1"),
        ], terms=["الملف التالف"]),
        Page("case-stale", "حالة 7 — نتيجة قديمة", [
            Img("images/test/K07_stale_banner.png", "تنبيه رمادي: النتيجة مش بتعكس آخر تعديل.", 1.0, 10),
            Field("إيه اللي حصل", "الموارد البشرية عدّلت إجابة بعد التقييم."),
            Field("النتيجة", "اتعلّمت «قديمة» وخرجت من الترتيب لحد ما تتعاد."),
            Field("في الاختبار", f"الدرجة كانت {k07.get('score_before', '—')} وبقت {k07.get('score_after', '—')} بعد إعادة التقييم، في الاختبار K07"),
            Field("نفس الفكرة", "اعتماد نسخة معايير جديدة بيعلّم كل النتائج القديمة، وزرار «إعادة تقييم القديم والفاشل» بيعالجها."),
            Tech([line("flag:stale"), line("flag:data_changed"), line("flag:duplicate"), line("field:Job Applicant.ai_data_hash")]),
        ], terms=["النتيجة القديمة"], ids=["flag:stale", "flag:data_changed", "flag:duplicate", "field:Job Applicant.ai_data_hash"]),
        Page("case-engine-down", "حالة 8 — المحرك واقف", [
            Img("images/test/K15_failed.png", "التقييم «فشل» والمحرك واقف، والطلب نفسه محفوظ.", 1.0, 10),
            Field("إيه اللي حصل", "وقّفنا المحرك عمدًا، وقدّمنا طلب جديد."),
            Field("الطلب", f"اتحفظ في {k15.get('saved_s', '—')} ثانية عادي جدًا."),
            Field("التقييم", f"بعد المحاولات المسموحة بقى «فشل» بعد {k15.get('failed_after_s', '—')} ثانية، ومحدش خسر طلبه."),
            Field("بعد ما المحرك رجع", f"زرار «إعادة المحاولة» خلّص التقييم في {k15.get('retry_s', '—')} ثانية."),
            Tech([line("setting:frappe:max_retries"), line("setting:engine-env:MAX_ATTEMPTS"), line("setting:frappe:timeout"), line("setting:frappe:request_timeout")]),
        ], terms=["المحرك واقف"], ids=["setting:frappe:max_retries", "setting:engine-env:MAX_ATTEMPTS", "setting:frappe:timeout", "setting:frappe:request_timeout"]),
    ]
    return Chapter("cases", "9 — الحالات الخاصة", pages, intro="كل حالة صعبة في صفحة: إيه اللي حصل، والنظام عمل إيه، وليه.")
