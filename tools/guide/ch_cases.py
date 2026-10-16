"""Chapter 9: special cases, one page each."""

from __future__ import annotations

from inv import line
from model import Chapter, Field, Img, Page, Tech


def _crit(case: dict, key: str) -> dict:
    return next((c for c in case.get("criteria", []) if c["key"] == key), {})


MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
BAND_AR = {"high": "مرتفعة", "medium": "متوسطة", "low": "منخفضة"}


def _count(n, one: str, two: str, few: str, many: str | None = None) -> str:
    """«طلب واحد»، «طلبين»، «3 طلبات»، «11 طلب» (Egyptian Arabic counting)."""
    n = int(n or 0)
    if n == 1:
        return f"{one} واحد"
    if n == 2:
        return two
    return f"{n} {few if 3 <= n <= 10 else (many or one)}"


def _day(value) -> str:
    """«16 أكتوبر 2026» from a Frappe date-time."""
    try:
        y, m, d = str(value)[:10].split("-")
        return f"{int(d)} {MONTHS[int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return "—"


def consent_pages(F: dict) -> list[Page]:
    """OPEN_QUESTIONS #20 and #21: the defaults decided by Nadine until the client confirms."""
    con = F.get("consent") or {}
    tt = F["tests"]["items"]
    pw, pr, wd = con.get("paper_waiting", {}), con.get("paper_recorded", {}), con.get("withdrawn", {})
    groups = con.get("groups", {})
    k16, k17 = tt.get("K16", {}), tt.get("K17", {})
    rc = pr.get("consent") or {}
    wc = wd.get("consent") or {}
    eng = wd.get("engine") or {}
    gone = (wd.get("engine_audit") or {}).get("erasure") or {}
    n_wait = len(groups.get("awaiting_consent", []))
    return [
        Page("case-paper", "حالة 9 أ — طلب ورقي من غير موافقة", [
            Img("images/steps/X_paper_awaiting.png", f"طلب {pw.get('name', '—')} الورقي: «بانتظار الموافقة» وزرار «تسجيل الموافقة».", 1.0, 10),
            Field("إيه اللي حصل", "موظف الموارد البشرية دخّل طلب ورقي بإيده من شاشة المتقدم، والطلب ده مفيهوش خانة الموافقة اللي في نموذج الموقع."),
            Field("النتيجة", "الطلب اتحفظ عادي بكل إجاباته، وحالة الذكاء بتاعته «بانتظار الموافقة»، ومفيش أي حاجة منه راحت للمحرك."),
            Field("في الاختبار", "الطلب الورقي فضل «بانتظار الموافقة»، ومن غير أي مهمة ذكاء." if k16.get("ok") else "—"),
            Field("القرار", "ده الافتراضي اللي نادين قررته لحد ما العميل يأكد، ومكتوب في السؤال 20."),
            Tech([line("status:ai_status:Awaiting Consent"), line("button:frappe:تسجيل الموافقة"), line("button:frappe-action:consent"), "test K16 — paper application, consent recorded by HR"]),
        ], terms=["الطلب الورقي", "بانتظار الموافقة"], ids=["status:ai_status:Awaiting Consent", "button:frappe:تسجيل الموافقة", "button:frappe-action:consent"]),
        Page("case-paper-group", "حالة 9 ب — الطلبات الورقية في الترتيب", [
            Img("images/steps/X_awaiting_group.png", "مجموعة «بانتظار الموافقة» في ترتيب الشاغر.", 1.0, 10),
            Field("بيظهر فين", f"في مجموعة «بانتظار الموافقة» تحت الترتيب، وفيها دلوقتي {_count(n_wait, 'طلب', 'طلبين', 'طلبات')}، من غير درجة."),
            Field("التنبيه", "فوق الترتيب سطر برتقالي بيقول عدد الطلبات المستنية موافقة، عشان محدش ينساها."),
            Field("ليه مش في «جاري المعالجة»", "لإنه مش بيتعالج أصلًا؛ هو مستني خطوة من الموارد البشرية."),
            Tech([line("status:group:awaiting_consent")]),
        ], terms=["مجموعة بانتظار الموافقة"], ids=["status:group:awaiting_consent"]),
        Page("case-paper-dialog", "حالة 9 ج — تسجيل الموافقة ومصدرها", [
            Img("images/steps/X_paper_dialog.png", "نافذة «تسجيل الموافقة»: المصدر إلزامي.", 0.8, 9),
            Field("إمتى", "لما المتقدم يكون وقّع موافقة برّه النظام، زي نموذج ورقي."),
            Field("المصدر", "خانة المصدر إلزامية، زي «ورقة موقّعة»، ومن غيرها الطلب بيترفض."),
            Field("بيتسجّل إيه", "اسم اللي سجّل الموافقة، ووقتها، ومصدرها، ونسخة نص الموافقة، وسطر في سجل التدقيق."),
            Field("بعدها", "التقييم بيبدأ لوحده، زي أي طلب جه من الموقع."),
            Field("في الاختبار", f"المصدر الفاضي اترفض، وبعد «ورقة موقّعة» النتيجة طلعت بعد {k16.get('seconds', '—')} ثانية." if k16.get("ok") else "—"),
            Tech([line("endpoint:frappe:record_consent"), line("field:Job Applicant.ai_consent_source"), line("field:Job Applicant.ai_consent_recorded_by"), "test K16 — empty source refused, then recorded"]),
        ], terms=["تسجيل الموافقة", "مصدر الموافقة"], ids=["endpoint:frappe:record_consent", "field:Job Applicant.ai_consent_source", "field:Job Applicant.ai_consent_recorded_by"]),
        Page("case-paper-recorded", "حالة 9 د — بعد تسجيل الموافقة", [
            Img("images/steps/X_paper_recorded.png", f"طلب {pr.get('name', '—')}: سطر «سجّل الموافقة» فوق التقييم.", 1.0, 10),
            Field("إيه اللي حصل", f"الموارد البشرية سجّلت موافقة {pr.get('name', '—')} من ورقة موقّعة، والتقييم اشتغل لوحده."),
            Field("النتيجة", f"درجته {pr['score']:g} وفئته {BAND_AR.get(pr.get('band'), '—')}، وترتيبه {pr.get('rank') or '—'} من {pr.get('ranked_total') or '—'}."
                  if pr.get("score") is not None else "—"),
            Field("مين وإمتى", f"اتسجّلت يوم {_day(rc.get('on'))}، والمصدر «{rc.get('source') or '—'}»، واللي سجّلها: {rc.get('recorded_by') or '—'}"),
        ], terms=["الموافقة المسجّلة"]),
        Page("case-paper-fields", "حالة 9 هـ — خانات الموافقة في الطلب", [
            Img("images/steps/X_paper_fields.png", f"خانات الموافقة في طلب {pr.get('name', '—')}.", 1.0, 10),
            Field("الخانات", "الموافقة على المعالجة، ونسخة الموافقة، وتاريخ الموافقة، ومصدر الموافقة، واللي سجّلها."),
            Field("للقراءة بس", "محدش بيكتب في الخانات دي بإيده: الزرار هو اللي بيملاها، وبيسجّل في سجل التدقيق."),
            Field("لطلب من الموقع", "خانة المصدر واللي سجّل بيفضلوا فاضيين، لإن المتقدم نفسه وافق في النموذج."),
        ], terms=["خانات الموافقة"]),
        Page("case-withdrawn", "حالة 10 أ — سحب الموافقة: برّه الترتيب", [
            Img("images/steps/X_withdrawn_group.png", f"مجموعة «مستبعد: سحب الموافقة»: {wd.get('name', '—')} من غير درجة.", 1.0, 10),
            Field("إيه اللي حصل", f"{wd.get('name', '—')} طلب يسحب موافقته، والموارد البشرية سجّلت ده بزرار «سحب موافقة المعالجة» وكتبت السبب."),
            Field("في الترتيب", "خرج من الترتيب فورًا، وبيظهر في مجموعة مقفولة، من غير درجة ولا تفاصيل."),
            Field("بنك المتقدمين", "بيظهر في المستبعدين بسبب «سحب موافقته على المعالجة» بس."),
            Field("في الاختبار", f"المتقدم خرج من الترتيب في {k17.get('seconds', '—')} ثانية، وملف سيرته اتمسح من المحرك." if k17.get("ok") else "—"),
            Field("القرار", "ده الافتراضي اللي نادين قررته لحد ما العميل يأكد، ومكتوب في السؤال 21."),
            Tech([line("status:group:consent_withdrawn"), line("status:ai_status:Consent Withdrawn"), "test K17 — consent withdrawn, AI data erased"]),
        ], terms=["سحب الموافقة", "مستبعد: سحب الموافقة"], ids=["status:group:consent_withdrawn", "status:ai_status:Consent Withdrawn"]),
        Page("case-withdrawn-applicant", "حالة 10 ب — سحب الموافقة: صفحة الطلب", [
            Img("images/steps/X_withdrawn_applicant.png", f"صفحة طلب {wd.get('name', '—')} بعد سحب الموافقة.", 1.0, 9),
            Field("اللي اتمسح من المحرك", "ملف السيرة ونصّه، والملف المنظّم، والفهرسة، وكل النتايج"
                  + (f"، يعني {_count(gone.get('documents'), 'ملف سيرة', 'ملفين سيرة', 'ملفات سيرة')} و{_count(gone.get('screenings'), 'تقييم', 'تقييمين', 'تقييمات')}."
                     if gone.get("documents") else f"، يعني {_count(gone.get('screenings'), 'تقييم', 'تقييمين', 'تقييمات')}، ومكانش عنده سيرة.")),
            Field("اللي فاضل في المحرك", "رقم الطلب بس، من غير مستندات ولا تقييمات ولا بيانات."
                  if not (eng.get("documents") or eng.get("screenings") or eng.get("facts")) else "—"),
            Field("اللي اتمسح من المنصة", "قسم تقييم الذكاء والأدلة وخانات الدرجة، والنتايج المكتوبة في سجل التدقيق؛ الأفعال نفسها فضلت في السجل."),
            Field("اللي فضل", f"الطلب الأصلي بإجاباته وملف سيرته في المنصة، وتاريخ السحب {_day(wc.get('withdrawn_on'))}."),
            Field("لو المحرك واقف", "الحذف بيتعاد لوحده كل دقيقتين لحد ما يتم، والطلب برّه الترتيب من أول لحظة."),
            Field("نهائي", "السحب نهائي للطلب ده؛ لو المتقدم رجع وافق، يقدّم طلب جديد."),
            Tech([line("field:Job Applicant.ai_erased_on"), line("hook:ido_talent_ai.screening.erase_pending"), line("status:ai_job:Cancelled")]),
        ], terms=["حذف بيانات الذكاء"], ids=["field:Job Applicant.ai_erased_on", "hook:ido_talent_ai.screening.erase_pending", "status:ai_job:Cancelled"]),
    ]


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
            Field("في الاختبار", "متقدم مصري طوله 172 طلع بسببين مكتوبين." if k02.get("ok") else "—"),
            Field("ليه «بحسب ما كتبه»", "النظام بيحكم على اللي المتقدم صرّح بيه، والموارد البشرية بتتأكد في المقابلة."),
            Tech(["test K02 — not eligible: height 172 and nationality Egypt"]),
        ], terms=["غير مستوفٍ"]),
        Page("case-needs-review", "حالة 2 — يحتاج مراجعة", [
            Img("images/steps/X_needs_review.png", f"خلاصة تقييم {nr['name']}: معيار إلزامي من غير إجابة.", 1.0, 11),
            Field("إيه اللي حصل", f"{nr['name']} ساب سؤال الإشراف فاضي، والإشراف معيار إلزامي، ومعندوش سيرة."),
            Field("النتيجة", "«يحتاج مراجعة»: النظام مش بيخمّن، وبيطلب من الموارد البشرية تبص بنفسها."),
            Field("وكمان", "طول فاضي من نظام بيسمح بكده بيدّي نفس النتيجة." if k03b.get("ok") else "قيمة ناقصة في شرط إلزامي بتدّي نفس النتيجة."),
            Field("الفرق عن غير مستوفٍ", "غير مستوفٍ معناه القيمة موجودة وغلط؛ يحتاج مراجعة معناه القيمة ناقصة."),
            Tech(["test K03a — blank height through the public form", "test K03b — blank height through the console"]),
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
            Field("في الاختبار", "مقارنة الحالتين لقت الفرق ده بالظبط." if tt.get("K04", {}).get("ok") else "—"),
            Tech(["test K04 — blank answer versus the answer 0"]),
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
            Field("وكمان", "ملف سيرة من النوع القديم كان بيوقّف التقييم، واتصلّح في الاختبار الشامل."),
            Tech(["test C08 — corrupt PDF", "bug F1 — an RTF CV failed the screening (fixed)"]),
        ], terms=["الملف التالف"]),
        Page("case-stale", "حالة 7 — نتيجة قديمة", [
            Img("images/test/K07_stale_banner.png", "تنبيه رمادي: النتيجة مش بتعكس آخر تعديل.", 1.0, 10),
            Field("إيه اللي حصل", "الموارد البشرية عدّلت إجابة بعد التقييم."),
            Field("النتيجة", "اتعلّمت «قديمة» وخرجت من الترتيب لحد ما تتعاد."),
            Field("في الاختبار", f"الدرجة كانت {k07.get('score_before', '—')} وبقت {k07.get('score_after', '—')} بعد إعادة التقييم."),
            Field("نفس الفكرة", "اعتماد نسخة معايير جديدة بيعلّم كل النتائج القديمة، وزرار «إعادة تقييم القديم والفاشل» بيعالجها."),
            Tech([line("flag:stale"), line("flag:data_changed"), line("flag:duplicate"), line("field:Job Applicant.ai_data_hash"), "test K07 — an answer edited after the evaluation"]),
        ], terms=["النتيجة القديمة"], ids=["flag:stale", "flag:data_changed", "flag:duplicate", "field:Job Applicant.ai_data_hash"]),
        Page("case-engine-down", "حالة 8 — المحرك واقف", [
            Img("images/test/K15_failed.png", "التقييم «فشل» والمحرك واقف، والطلب نفسه محفوظ.", 1.0, 10),
            Field("إيه اللي حصل", "وقّفنا المحرك عمدًا، وقدّمنا طلب جديد."),
            Field("الطلب", f"اتحفظ في {k15.get('saved_s', '—')} ثانية عادي جدًا."),
            Field("التقييم", f"بعد المحاولات المسموحة بقى «فشل» بعد {k15.get('failed_after_s', '—')} ثانية، ومحدش خسر طلبه."),
            Field("بعد ما المحرك رجع", f"زرار «إعادة المحاولة» خلّص التقييم في {k15.get('retry_s', '—')} ثانية."),
            Tech([line("setting:frappe:max_retries"), line("setting:engine-env:MAX_ATTEMPTS"), line("setting:frappe:timeout"), line("setting:frappe:request_timeout"), "test K15 — engine stopped: apply, then retry"]),
        ], terms=["المحرك واقف"], ids=["setting:frappe:max_retries", "setting:engine-env:MAX_ATTEMPTS", "setting:frappe:timeout", "setting:frappe:request_timeout"]),
    ] + consent_pages(F)
    return Chapter("cases", "9 — الحالات الخاصة", pages, intro="كل حالة صعبة في صفحة: إيه اللي حصل، والنظام عمل إيه، وليه.")
