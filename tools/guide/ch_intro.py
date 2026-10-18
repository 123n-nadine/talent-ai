"""Chapters 1–4: one-page summary, how to talk to the manager, the big picture, roles."""

from __future__ import annotations

from inv import line
from model import Bullets, Chapter, Diagram, Field, Img, Note, P, Page, Rule, Table, Tech


def pct(x) -> str:
    return f"{x:g}%"


def summary(F: dict) -> Chapter:
    t = F["tests"]
    ex = F["example"]
    rk = F["ranking"]
    return Chapter("summary", "1 — الملخص في صفحة واحدة", [Page("summary-page", "الفكرة كلها", [
        Rule("الذكاء الاصطناعي يرشّح ويشرح، والقرار للـ HR"),
        P("لما مئات الناس يقدّموا على وظيفة واحدة، فريق الموارد البشرية مش هيلحق يقرا كل طلب بنفس التركيز.\n"
          "النظام ده بيقرا كل طلب لوحده، ويقارنه بمعايير اعتمدها فريق الموارد البشرية قبلها.\n"
          "بعد كده بيدّي كل متقدم درجة من 100، ويرتّبهم، ويكتب ليه."),
        Field("بيعمل إيه", "بيتأكد من الشروط الإلزامية بالكود، زي الجنسية والطول والوزن والسن."),
        Field("وكمان", "بيحكم على كل معيار بمستوى ثابت (0 أو 25 أو 50 أو 75 أو 100) ومعاه دليل."),
        Field("الدليل", "إجابة المتقدم في نموذج التقديم، أو جملة منقولة بالحرف من سيرته الذاتية."),
        Field("مش بيعمل", "عمره ما بيقبل ولا بيرفض حد، ولا بيغيّر حالة أي طلب."),
        Field("القرار", "موظف الموارد البشرية بس يقدر يرشّح أو يعلّق أو يرفض، ولازم يكتب السبب."),
        P(f"مثال حقيقي من الديمو: {ex['name']} اتقيّم {ex['score']:g} من 100، وترتيبه {ex['rank']} من {ex['ranked_total']}.\n"
          f"الشاغر فيه {rk.get('applicants_total') or rk['total']} طلب وهمي، منهم {(F.get('consent') or {}).get('paper_count', 0)} طلب ورقي دخّلته الموارد البشرية."),
        P(f"الاختبار الشامل الأخير عدّى {t['passed']} من {t['total']} فحص في متصفح حقيقي، بكل الأدوار وكل أنواع السير الذاتية."),
        Note("كل الأسماء والأرقام في الدليل ده وهمية، ومفيش أي بيانات لأشخاص حقيقيين.", "ok"),
    ], terms=["الذكاء الاصطناعي", "الموارد البشرية", "المعايير", "الدليل", "الدرجة"])])


def manager(F: dict) -> Chapter:
    ev = F["evaluation"]
    r8 = ev["runs"].get("8B v1 r8") or ev["runs"].get("8B v1 r7") or ev["runs"].get("8B v1 r6") or ev["runs"]["8B v1"]  # the latest gold-set run
    sp = ev.get("split") or {}
    code, model = sp.get("code", {}), sp.get("model", {})
    thr = ev["throughput"]
    tt = F["tests"]["items"]
    c_scan, c_pdf, c_none = tt.get("C01", {}), tt.get("C02", {}), tt.get("C07", {})
    k15 = tt.get("K15", {})
    perm_users = len(F["tests"]["perm"].get("users", []))
    b8 = dict((ev.get("bench") or {}).get("8", {}))
    b8["pipeline_mean_s"] = round(b8.get("pipeline_mean_s", 0), 1)  # one decimal, as in the evaluation report
    t_none = c_none.get("timing", {}).get("until_result_s", "—")
    t_scan = c_scan.get("timing", {}).get("until_result_s", "—")
    pts = [
        f"الوقت: ألف متقدم بياخدوا حوالي ساعة بثمانية عمّال ({thr['8']['per1000_min']} دقيقة)، وحوالي ساعة وتلت بأربعة ({thr['4']['per1000_min']} دقيقة).\n"
        f"الطلب الواحد بياخد من {t_none} ثانية من غير سيرة لـ {t_scan} ثانية بصورة ممسوحة، والألف أسرع من مجموعهم لإن العمّال بيشتغلوا على طلبات مختلفة في نفس الوقت.\n"
        f"الرقم ده من اختبار {b8.get('n', '—')} طلب مضروب في عشرة: {b8.get('without_cv', '—')} من غير سيرة، و{b8.get('with_cv', '—')} بسيرة نصية، ومفيش صور ممسوحة؛ "
        f"متوسط معالجة الطلب فيه {b8.get('pipeline_mean_s', '—')} ثانية بثمانية عمّال، و{b8.get('n', '—')} طلب × {b8.get('pipeline_mean_s', '—')} ثانية ÷ 8 عمّال = {round(b8.get('n', 0) * b8.get('pipeline_mean_s', 0) / 8)} ثانية، "
        f"والمقاس فعلًا {round(b8.get('processing_wall_s', 0))} ثانية من آخر إرسال لآخر نتيجة.",
        f"الدقة: على {ev['gold']} متقدم اختبار، النظام جاب المستوى المتوقع حسب جدول المعايير في {pct(r8['exact'])} من المعايير؛ المستوى المتوقع محسوب من الجدول بالكود، مش تقييم بشري.\n"
        f"جزء الكود (الإجابات الرقمية والاختيارية): {code.get('exact', '—')}% من {code.get('n', '—')} حكم. "
        f"جزء النموذج اللغوي (النص الحر وجانب السيرة): {model.get('exact', '—')}% بالظبط و{model.get('within', '—')}% في حدود خطوة من {model.get('n', '—')} حكم، "
        f"على {ev.get('distinct_free_texts', '—')} نصوص حرة و{ev.get('cv_documents', '—')} سيرة.",
        (f"القرب: الباقي كله كان على بُعد درجة واحدة بس، يعني {pct(r8['within_one'])} في حدود خطوة."
         if r8["within_one"] >= 100
         else f"القرب: {pct(r8['within_one'])} من الأحكام في حدود خطوة واحدة؛ الأبعد الوحيد رخصة قراها النموذج من السيرة بصرامة، وعلّمها تعارض وبعتها للمراجعة."),
        f"الأدلة: {pct(r8['evidence'])} من الأحكام اللي فوق الصفر ليها دليل اتراجع بالكود.",
        f"الشروط: القواعد الإلزامية اتطبقت صح في {pct(r8['eligibility'])} من الحالات، والنموذج اللغوي مش بيشوفها أصلًا.",
        f"العدل: تغيير اسم المتقدم ما غيّرش ولا مستوى في {ev['name_swap_pct']}% من الحالات.",
        f"الثبات: نفس الطلب لما اتعاد تقييمه طلّع نفس النتيجة في {ev['rerun_pct']}% من الحالات"
        + (f"؛ طلب واحد من {ev['gold']} فشل تقييمه (خطأ في قراءة السيرة من النموذج بعد تلات محاولات) وبيظهر «فشل» مع رسالة الخطأ." if ev.get('failed') else "."),
        f"السرعة لكل طلب: من غير سيرة {c_none.get('seconds', '—')} ثانية، وبسيرة نصية {c_pdf.get('seconds', '—')} ثانية، وبصورة ممسوحة {c_scan.get('seconds', '—')} ثانية.",
        f"الاعتمادية: وقّفنا المحرك وقدّمنا طلب، فاتحفظ في {k15.get('saved_s', '—')} ثانية، ورجع اتقيّم بعد إعادة المحاولة في {k15.get('retry_s', '—')} ثانية.",
        f"الصلاحيات: جرّبنا {perm_users} أنواع مستخدمين، ومحدش غير الموارد البشرية شاف درجة أو سيرة.",
    ]
    return Chapter("manager", "2 — إزاي تكلّمي مديرك: عشر نقاط بالأرقام", [Page("manager-page", "عشر نقاط من الاختبارات الحقيقية", [
        P("النقط دي جاية من تقرير التقييم ومن الاختبار الشامل، مش من تقدير.\n"
          "مصدر كل رقم مكتوب في فصل نتائج الاختبارات."),
        Bullets(pts, numbered=True),
        Note("الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة.", "warn"),
    ], terms=["العمّال", "النموذج اللغوي", "إعادة المحاولة"], ids=["evaluation:run:8B v1 r8", "evaluation:throughput:4", "evaluation:throughput:8", "evaluation:rerun", "evaluation:name-swap"])])


DIAGRAM_SVG = """<svg viewBox="0 0 1000 620" xmlns="http://www.w3.org/2000/svg" font-family="IBM Plex Sans Arabic" direction="rtl">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1e4db5"/></marker></defs>
<style>.box{fill:#fff;stroke:#1e4db5;stroke-width:2}.t{font-size:22px;font-weight:700;fill:#1f2b47;text-anchor:middle}.s{font-size:14px;fill:#56627c;text-anchor:middle}
.ok{font-size:13px;fill:#166c3c;text-anchor:middle}.no{font-size:13px;fill:#b42525;text-anchor:middle}.ln{stroke:#1e4db5;stroke-width:2.5;fill:none;marker-end:url(#a)}</style>
<rect class="box" x="760" y="40" width="210" height="90" rx="14"/><text class="t" x="865" y="80">المتقدم</text><text class="s" x="865" y="108">نموذج التقديم العام</text>
<rect class="box" x="760" y="250" width="210" height="110" rx="14"/><text class="t" x="865" y="292">Frappe HR</text><text class="s" x="865" y="320">الطلبات · الشاشات · القرار</text><text class="s" x="865" y="342">الهوية الكاملة هنا بس</text>
<rect class="box" x="400" y="250" width="230" height="110" rx="14"/><text class="t" x="515" y="292">المحرك</text><text class="s" x="515" y="320">الشروط · الأدلة · الدرجة</text><text class="s" x="515" y="342">Talent Engine</text>
<rect class="box" x="40" y="250" width="230" height="110" rx="14"/><text class="t" x="155" y="292">النموذج اللغوي</text><text class="s" x="155" y="320">على نفس السيرفر</text><text class="s" x="155" y="342">Qwen3-8B</text>
<rect class="box" x="400" y="470" width="230" height="90" rx="14"/><text class="t" x="515" y="508">قراءة الصور</text><text class="s" x="515" y="534">OCR على المعالج</text>
<rect class="box" x="760" y="470" width="210" height="90" rx="14"/><text class="t" x="865" y="508">الموارد البشرية</text><text class="s" x="865" y="534">بتقرر وتكتب السبب</text>
<path class="ln" d="M865,130 L865,245"/><text class="ok" x="700" y="175">بيوصل: الإجابات والشروط والسيرة والموافقة</text>
<path class="ln" d="M755,290 L635,290"/><text class="ok" x="695" y="230">بيوصل: الإجابات · الجنسية والسن والطول والوزن</text><text class="ok" x="695" y="248">بصمة الهوية بدل رقمها · ملف السيرة</text>
<text class="no" x="695" y="388">مش بيوصل أبدًا: رقم الهوية · البريد · الجوال</text><text class="no" x="695" y="406">ولا تاريخ الميلاد (السن بس)</text>
<path class="ln" d="M395,290 L275,290"/><text class="ok" x="335" y="230">بيوصل: نص السيرة بعد الإخفاء</text><text class="ok" x="335" y="248">والإجابات النصية والمعايير</text>
<text class="no" x="335" y="388">مش بيوصل: الاسم ولا الهوية ولا الجنسية</text><text class="no" x="335" y="406">ولا الجنس ولا السن ولا الصورة</text>
<path class="ln" d="M275,325 L395,325"/>
<path class="ln" d="M515,365 L515,465"/><path class="ln" d="M545,465 L545,365"/>
<path class="ln" d="M635,335 L755,335"/><text class="ok" x="695" y="452">بيرجع بتوقيع: الدرجة والمستويات</text><text class="ok" x="695" y="470">والأدلة والوسوم والترتيب</text>
<path class="ln" d="M865,365 L865,465"/>
</svg>"""


def big_picture(F: dict) -> Chapter:
    return Chapter("picture", "3 — الصورة الكبيرة: مين بيكلّم مين", [Page("picture-page", "الرحلة في رسمة واحدة", [
        Diagram(DIAGRAM_SVG, "images/diagram.png", "الأسهم الخضرا اللي بيتبعت، والأحمر اللي عمره ما بيتبعت."),
        P("المنصة هنا هي نظام الموارد البشرية اللي العميل شغال عليه، واسمها Frappe HR\n"
          "المتقدم بيملا نموذج التقديم العام، والطلب بيتحفظ في المنصة على طول.\n"
          "بعدها المنصة بتبعت للمحرك الإجابات والحقائق المسموحة بس، من غير الهوية.\n"
          "المحرك بيخفي الاسم والأرقام من السيرة قبل ما أي نموذج لغوي يقراها.\n"
          "النتيجة بترجع للمنصة بتوقيع سرّي، عشان محدش يقدر يزوّرها.\n"
          "آخر خطوة دايمًا عند الموارد البشرية: هي اللي بتقرر وبتكتب السبب."),
        Tech([line("architecture:adapter"), line("architecture:tenant"), line("security:hmac-callback"), line("security:id-token"),
              line("security:no-sensitive-facts"), line("architecture:service:api"), line("architecture:service:worker"),
              line("architecture:service:vllm"), line("architecture:service:embed"), line("architecture:service:db"), line("architecture:service:redis")]),
    ], terms=["المحرك", "Frappe", "بصمة الهوية", "التوقيع"], ids=["architecture:adapter", "architecture:tenant", "security:hmac-callback", "security:id-token",
                                                       "security:no-sensitive-facts", "architecture:service:api", "architecture:service:worker",
                                                       "architecture:service:vllm", "architecture:service:embed", "architecture:service:db", "architecture:service:redis"])])


ROLE_TEXT = {
    "administrator": ("مدير الموقع", "بيشوف كل حاجة ويقدر يعمل كل حاجة، زي الموارد البشرية بالظبط."),
    "system_manager": ("مدير النظام", "بيشوف التقييم ويقدر ياخد قرار، ويقدر يعدّل الإعدادات."),
    "hr_manager": ("مدير الموارد البشرية", "بيعتمد المعايير، ويشوف الترتيب، وياخد القرار، ويعدّل الإعدادات."),
    "hr_user": ("أخصائي التوظيف", "نفس شغل المدير في الطلبات والقرارات، بس الإعدادات مقفولة عليه."),
    "interviewer": ("المقابِل", "بيعمل المقابلات بس، ومش بيشوف أي درجة أو تقييم أو سيرة."),
    "employee": ("الموظف العادي", "مش بيشوف أي حاجة من التوظيف خالص."),
    "ess": ("موظف الخدمة الذاتية", "بيدخل على خدماته الشخصية بس، والتوظيف كله ممنوع عليه."),
    "portal": ("متقدم عنده حساب", "بيقدّم من الموقع، ومش بيقدر يفتح طلبه ولا طلب حد تاني جوه النظام."),
    "guest": ("زائر من غير حساب", "بيشوف صفحة الوظائف ونموذج التقديم بس."),
}
STATE = {"see": "يشوف", "edit": "يعدّل", "deny": "ممنوع", "?": "—"}


def roles(F: dict) -> list[Chapter]:
    perm = F["tests"]["perm"]
    users = perm.get("users", [])
    m = perm.get("matrix", {})
    rows = [[ROLE_TEXT[u["key"]][0], ", ".join(r.split(" (")[0] for r in u["roles"]), ROLE_TEXT[u["key"]][1]] for u in users]
    ch4 = Chapter("roles", "4 — الأدوار: مين يعمل إيه", [Page("roles-table", "جدول الأدوار", [
        P("كل مستخدم في المنصة ليه دور أو أكتر، والدور هو اللي بيحدد هيشوف إيه.\n"
          "حقول الذكاء كلها في مستوى صلاحية خاص، مفتوح للموارد البشرية ومدير النظام بس."),
        Table(["الدور", "اسمه في النظام", "بيعمل إيه"], rows, ltr_cols=(1,), widths=(0.22, 0.3, 0.48)),
        Note(perm.get("not_found_ar", "مفيش في المنصة دور اسمه «مدير التوظيف»، فمدير القسم بيبقى موظف وممكن يكون مقابِل كمان."), "info"),
        Tech([line(f"role:{r}") for r in ("HR Manager", "HR User", "System Manager", "Administrator", "Interviewer", "Employee", "Employee Self Service", "Guest", "Website User")]
             + [line("security:permlevel"), line("security:require-hr")]),
    ], terms=["الدور", "مستوى الصلاحية"], ids=[f"role:{r}" for r in ("HR Manager", "HR User", "System Manager", "Administrator", "Interviewer", "Employee", "Employee Self Service", "Guest", "Website User")]
       + ["security:permlevel", "security:require-hr"])])
    # «النظام من عين كل واحد»: one page per role + the comparison table
    DISTINCT = {
        "administrator": ("audit", "سجل التدقيق كامل: كل إجراء باسم صاحبه، وده اللي بيميّز الإدارة."),
        "system_manager": ("settings", "شاشة الإعدادات: مدير النظام بيعدّل ربط المحرك وإعداداته."),
        "hr_manager": ("assessment", "طلب متقدم بأزرار القرار وإلغاء الحكم: ده اللي بيقرر."),
        "hr_user": ("settings", "الرسالة اللي بتظهر له لما يحاول يفتح الإعدادات: مرفوض، وباقي شاشات التوظيف مفتوحة له."),
    }
    pages = []
    for u in users:
        key = u["key"]
        row = m.get(key, {})
        sees = [s["label"] for s in perm["screens"] if row.get(s["key"], {}).get("state") in ("see", "edit")]
        denied = [s["label"] for s in perm["screens"] if row.get(s["key"], {}).get("state") == "deny"]
        # one picture per role that shows what sets it apart (the HR roles would otherwise share one)
        pick = DISTINCT.get(key)
        shot = (row.get(pick[0], {}).get("shot") if pick else None) or (row.get("assessment", {}).get("shot") if row.get("assessment", {}).get("state") in ("see", "edit") else (row.get("applicant", {}).get("shot") or row.get("home", {}).get("shot")))
        roles_txt = "، ".join(r.split(" (")[0] for r in u["roles"])
        blocks = [Field("الدور", ROLE_TEXT[key][1]), Field("بيدخل بـ", roles_txt if key != "guest" else "من غير تسجيل دخول")]
        blocks.append(Field("بيشوف", "، ".join(x.replace("Talent Console", "الكونسول") for x in sees) or "ولا شاشة من شاشات التوظيف"))
        if denied:
            blocks.append(Field("ممنوع عليه", "، ".join(x.replace("Talent Console", "الكونسول") for x in denied)))
        if shot:
            cap = pick[1] if pick else ("اللي بيظهر له لما يفتح طلب متقدم." if row.get("assessment", {}).get("state") in ("see", "edit") else "الرسالة اللي بتظهر له لما يحاول يفتح شاشة توظيف.")
            blocks.append(Img(shot.replace("guide/", ""), cap, 0.9, 11.5))
        pages.append(Page(f"role-{key}", f"من عين {ROLE_TEXT[key][0]}", blocks, terms=[ROLE_TEXT[key][0]], ids=[f"role:user:{u['login']}"] if u.get("login") and "@" in u.get("login", "") else []))
    head = ["الشاشة"] + [ROLE_TEXT[u["key"]][0] for u in users]
    trows = [[s["label"].replace("Talent Console", "الكونسول")] + [STATE.get(m.get(u["key"], {}).get(s["key"], {}).get("state", "?"), "—") for u in users] for s in perm.get("screens", [])]
    pages.append(Page("role-compare", "المقارنة: الأدوار في الأعمدة والشاشات في الصفوف", [
        P("الجدول جاي من الاختبار الشامل نفسه: كل خانة اتفتحت فعلًا بالمستخدم ده واتصوّرت."),
        Table(head, trows, small=True),
        P("يشوف معناها بيفتح الشاشة ويقرا بس، ويعدّل معناها بيقدر ياخد إجراء، وممنوع معناها النظام رفض."),
    ], terms=["يشوف", "يعدّل", "ممنوع"]))
    ch4b = Chapter("eyes", "5 — النظام من عين كل واحد", pages, intro="كل صفحة هنا بتورّي النظام زي ما مستخدم واحد بيشوفه بالظبط.")
    return [ch4, ch4b]
