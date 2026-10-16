"""Chapter 7: the 10 processing stages (one page each) and the CV analysis pages."""

from __future__ import annotations

from inv import line
from model import Chapter, Field, Img, Page, Tech

STAGE_TEXT = {
    "intake": ("المحرك بيستلم الطلب، ويتأكد إن فيه موافقة وإن نسخة المعايير معتمدة.",
               "رقم المتقدم، والشاغر، ونسخة المعايير.", "معالجة جديدة بحالة «في الطابور».",
               "لو الموافقة مسحوبة، المعالجة مش بتبدأ خالص."),
    "answers": ("الإجابات بتترتب: الأرقام أرقام، والاختيارات من القائمة، والفراغ فراغ.",
                "إجابات نموذج التقديم.", "إجابات منظمة، وعدد اللي اتجاوب.",
                "الفراغ معناه «لم يُجب»، والصفر إجابة حقيقية، وده بيفرق في الدرجة."),
    "cv_text": ("الكلام بيتطلع من السيرة حسب نوعها: من الملف مباشرة، أو من ملف وورد، أو بعد تحويل الملفات القديمة، أو بالقراءة الضوئية للصور.",
                "ملف السيرة لو موجود.", "نص السيرة، وعدد الصفحات، ونسبة الثقة لو كانت صورة.",
                "ملف تالف أو مقفول بكلمة سر بيتعلّم «غير مقروء»، والتقييم بيكمّل من الإجابات.\nالسطر اللي القراءة الضوئية مش واثقة فيه (أقل من 80%) بيتشال من النص قبل النموذج، ومش بيتقبل كدليل أبدًا."),
    "redaction": ("الاسم والهاتف والبريد ورقم الهوية وتاريخ الميلاد والجنسية والجنس والعنوان بيتبدّلوا برموز.",
                  "نص السيرة الأصلي، واسم المتقدم كتلميح.", "نص مخفي الهوية، وعدد اللي اتشال من كل نوع.",
                  "النموذج اللغوي عمره ما بيشوف النص قبل الخطوة دي.\nوفي بوابة تانية قبل النموذج: أي حاجة لسه شكلها بريد أو رقم طويل بتتشال وبتتسجّل، حتى لو الاستخراج لخبط ترتيبها."),
    "profile": ("النموذج اللغوي بيقرا النص المخفي ويطلّع منه الخبرات والشهادات والمهارات واللغات والتعليم.",
                "النص المخفي الهوية بس.", "ملف منظم، كل عنصر فيه معاه الجملة اللي جه منها.",
                "لو مفيش سيرة، الخطوة دي بتتخطّى وبيتكتب السبب."),
    "evidence_check": ("الكود بيراجع كل عنصر: الجملة لازم تكون موجودة بالحرف في السيرة، وإلا العنصر بيتشال.",
                       "الملف المنظم والنص المخفي.", "عناصر متحقق منها، وسنين الخبرة محسوبة من التواريخ.",
                       "سنين الخبرة والإشراف بيحسبها الكود من التواريخ، مش النموذج."),
    "eligibility": ("الكود بيقارن اللي المتقدم كتبه بالشروط الإلزامية: الجنسية والطول والوزن والسن.",
                    "الحقائق المسموحة بس.", "مستوفٍ، أو غير مستوفٍ بحسب ما كتبه، أو يحتاج مراجعة.",
                    "قيمة ناقصة معناها «يحتاج مراجعة»، مش «غير مستوفٍ»."),
    "judgement": ("كل معيار بياخد مستوى من الخمسة: الإجابات المنظمة بالكود، والنصوص والسيرة بالنموذج اللغوي.",
                  "الإجابات، والملف المتحقق منه، وسلّم التقييم.", "مستوى ودليل لكل معيار.",
                  "لو الإجابة والسيرة اختلفوا، بيتاخد المستوى الأقل ويتعلّم «تعارض»."),
    "scoring": ("الدرجة بتتحسب بالكود من الأوزان والمستويات، ومعاها التغطية والفئة والترتيب.",
                "المستويات والأوزان.", "الدرجة من 100، والتغطية، والفئة، والترتيب.",
                "معيار إلزامي في المستوى صفر بيخلي الفئة «منخفضة» مهما كانت الدرجة."),
    "index": ("الملف المتحقق منه بيتحفظ في بنك المتقدمين، عشان يتقترح في شواغر بعدين.",
              "الملف المتحقق منه، من غير الاسم ولا الهوية.", "متجه بحث محفوظ.",
              "مفيش فهرسة لو الموافقة مسحوبة أو مدة الاحتفاظ خلصت."),
}

RED_AR = {"name": "الاسم", "phone": "الهاتف", "email": "البريد", "national_id": "رقم الهوية", "dob": "تاريخ الميلاد", "age": "العمر",
          "nationality": "الجنسية", "gender": "الجنس", "address": "العنوان", "url": "رابط"}

STAGE_IDS = {
    "intake": ["stage:intake"],
    "answers": ["stage:answers", "flag:missing_evidence"],
    "cv_text": ["stage:cv_text", "flag:cv_unreadable", "flag:low_ocr_confidence", "setting:engine-env:OCR_PROVIDER", "setting:engine-env:OCR_MIN_CONFIDENCE",
                "setting:engine-env:OCR_THREADS", "setting:engine-env:MAX_UPLOAD_MB", "field:Job Applicant.ai_cv_note", "field:Job Applicant.ai_cv_sha"],
    "redaction": ["stage:redaction", "security:redaction", "flag:redaction_guard", "command:script:talent-engine/scripts/reprocess_cvs.py"],
    "profile": ["stage:profile", "setting:engine-env:AI_PROVIDER", "setting:engine-env:LLM_MODEL", "setting:engine-env:LLM_BASE_URL", "setting:engine-env:VLLM_MODEL"],
    "evidence_check": ["stage:evidence_check", "flag:evidence_mismatch", "evaluation:quote-ratio"],
    "eligibility": ["stage:eligibility", "status:eligibility:eligible", "status:eligibility:not_eligible", "status:eligibility:needs_review", "setting:frappe:allowed_facts",
                    "setting:engine-env:ALLOWED_FACTS", "decision:claude:3"],
    "judgement": ["stage:judgement", "flag:contradiction", "flag:mandatory_zero", "flag:mandatory_missing", "setting:frappe:judge_prompt"],
    "scoring": ["stage:scoring", "status:band:high", "status:band:medium", "status:band:low", "flag:low_coverage", "field:Job Applicant.ai_flags"],
    "index": ["stage:index", "setting:engine-env:EMBEDDING_PROVIDER", "setting:engine-env:EMBEDDING_MODEL", "setting:engine-env:EMBEDDING_BASE_URL", "setting:frappe:retention_days",
              "setting:engine-env:RETENTION_DAYS_DEFAULT"],
}


def stages(F: dict) -> Chapter:
    ex = F["example"]
    pages = []
    for i, st in enumerate(ex["stages"], 1):
        key = st["key"]
        what, inp, out, edge = STAGE_TEXT[key]
        ms = st.get("ms")
        took = "أقل من جزء من الثانية" if not ms else (f"{ms / 1000:.1f} ثانية" if ms >= 1000 else f"{ms} جزء من الألف من الثانية")
        blocks = [
            Img(f"images/steps/S06_stage_{i:02d}.png", f"كارت المرحلة {i} في طلب {ex['name']}.", 0.45, 6.5),
            Field("بتعمل إيه", what),
            Field("بتاخد إيه", inp),
            Field("بتطلّع إيه", out),
            Field(f"في طلب {ex['name']}", (st.get("note") or "خلصت من غير ملاحظة").replace(" (OCR)", "") + f"، وخدت {took}."),
            Field("خلي بالك", edge),
            Tech([line(x) for x in STAGE_IDS[key]]),
        ]
        pages.append(Page(f"stage-{key}", f"المرحلة {i} — {st['label']}", blocks, terms=[st["label"]], ids=STAGE_IDS[key]))
    ca = F.get("cv_analysis", {})
    sc, pdf, word = ca.get("scan", {}), ca.get("pdf", {}), ca.get("word", {})
    pages += [
        Page("cv-scan", "تحليل السيرة 1 — صورة ممسوحة ومربعات القراءة", [
            Img("images/steps/CV_scan.png", "سيرة ممسوحة: كل سطر عليه مربع بلون الثقة.", 1.0, 13),
            Field("إيه ده", "الصورة الأصلية للسيرة، وفوقها مربع لكل سطر اتقرا بالقراءة الضوئية."),
            Field("الألوان", "الأخضر ثقة 90% أو أكتر، والأصفر من 80 لـ 89، والأحمر أقل من 80، والبنفسجي دليل متحدد."),
            Field("في الديمو", f"سيرة {ex['name']} اتقرت بثقة {round((sc.get('confidence') or 0) * 100)}% في {sc.get('lines', '—')} سطر."),
            Field("تجربة صعبة", "صورة مشوّشة عمدًا اتقرت بثقة 79%، فاتعلّمت «ثقة منخفضة» وراحت «يحتاج مراجعة»."),
            Tech([line("endpoint:engine:GET /v1/candidates/{ref}/cv/pages/{page}"), line("evaluation:ocr-threshold"), line("decision:claude:9")]),
        ], terms=["القراءة الضوئية", "الثقة"], ids=["evaluation:ocr-threshold", "decision:claude:9"]),
        Page("cv-pdf", "تحليل السيرة 2 — ملف بي دي إف فيه نص", [
            Img("images/steps/CV_pdf.png", "سيرة بي دي إف فيها نص: القراءة مباشرة من غير قراءة ضوئية.", 1.0, 13),
            Field("إيه الفرق", "الملف ده فيه نص حقيقي، فبيتقرا مباشرة وبثقة كاملة."),
            Field("في الديمو", f"سيرة {F['cases']['strong']['name']}: {pdf.get('lines', '—')} سطر في {pdf.get('pages', '—')} صفحة."),
            Field("العربي والإنجليزي", "سطور العربي بتترتب صح من اليمين للشمال، حتى لو جوه الملف مقلوبة."),
            Tech([line("decision:progress:Layout in display pixels")]),
        ], terms=["ملف نصي"], ids=["decision:progress:Layout in display pixels"]),
        Page("cv-word", "تحليل السيرة 3 — ملف Word", [
            Img("images/steps/CV_word.png", "سيرة وورد بعد ما اتحوّلت لصفحة.", 1.0, 13),
            Field("إيه اللي بيحصل", "ملف الوورد بيتقرا نصه مباشرة، والصفحة بتترسم عشان الموظف يشوف الأصل."),
            Field("الملفات القديمة", "بتتحوّل الأول، وبعدها بتتقرا عادي، وصيغها DOC وRTF"),
            Field("في الديمو", "ملف الوورد والملفين القديمين خلصوا كلهم بدرجة كاملة، في الاختبارات C04 وC05 وC06"),
        ], terms=["ملف Word"]),
        Page("cv-redaction", "تحليل السيرة 4 — إخفاء الهوية قبل وبعد", [
            Img("images/steps/CV_redaction.png", "عمودين: النص زي ما اتقرا، والنص اللي بيوصل للنموذج اللغوي.", 1.0, 13),
            Field("إيه ده", "كل سطر قبل وبعد؛ الرموز الحمرا مكان البيانات اللي اتشالت."),
            Field("في الديمو", f"سيرة {ex['name']} اتشال منها " + "، ".join(f"{RED_AR.get(k, k)} ({v})" for k, v in (sc.get("redaction") or {}).items()) + "."),
            Field("ليه مهم", "النموذج اللغوي بيشوف العمود الشمال بس، فمستحيل يتأثر بالاسم أو الجنسية."),
            Tech([line("decision:claude:4"), line("decision:progress:Redaction keeps line breaks")]),
        ], terms=["إخفاء الهوية"], ids=["decision:claude:4", "decision:progress:Redaction keeps line breaks"]),
    ]
    return Chapter("stages", "7 — المراحل العشرة وتحليل السيرة", pages, intro=f"كل مرحلة في صفحة، بنفس طلب {ex['name']} من الديمو.")
