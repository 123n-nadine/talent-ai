"""One Arabic line for every inventory item that has no narrative page of its own (the appendix
tables), following the writing rules (Arabic first, English only at the end of the line)."""

from __future__ import annotations

DOCTYPE = {
    "AI Applicant Answer": "سطر إجابة واحد في طلب المتقدم",
    "AI Assessment Evidence": "سطر دليل لكل معيار في تقييم المتقدم",
    "AI Candidate Assessment": "تقييم المتقدم المحفوظ في Frappe",
    "AI Job Criterion": "معيار واحد جوه ملف المعايير",
    "AI Job Profile": "ملف معايير الوظيفة",
    "AI Job Profile Version": "نسخة معتمدة ثابتة من ملف المعايير",
    "AI Job Question": "سؤال من أسئلة نموذج التقديم",
    "AI Job Rule": "شرط إلزامي في ملف المعايير",
    "AI Recruitment Audit Log": "سجل التدقيق",
    "AI Recruitment Job": "مهمة معالجة لطلب واحد",
    "AI Recruitment Settings": "إعدادات الربط بالمحرك",
}

FIELD = {
    "ai_enabled": "تشغيل الفرز الذكي للشاغر", "ai_profile": "ملف المعايير المربوط بالشاغر", "ai_profile_approved": "هل الملف المربوط معتمد",
    "ai_links": "روابط سريعة للترتيب والمتابعة", "nationality": "الجنسية اللي كتبها المتقدم", "date_of_birth": "تاريخ الميلاد، والمحرك بياخد السن بس",
    "id_type": "نوع الهوية", "national_id": "رقم الهوية، مقفول على الموارد البشرية ومش بيتبعت", "height_cm": "الطول بالسنتيمتر", "weight_kg": "الوزن بالكيلو",
    "ai_consent": "موافقة المتقدم على المعالجة", "ai_consent_version": "نسخة نص الموافقة", "ai_consent_on": "وقت الموافقة",
    "ai_consent_withdrawn_on": "وقت سحب الموافقة", "ai_answers": "جدول إجابات الفرز", "ai_html": "قسم تقييم الذكاء في الطلب",
    "ai_status": "حالة المعالجة", "ai_score": "الدرجة من 100", "ai_band": "الفئة", "ai_eligibility": "الأهلية", "ai_coverage": "التغطية",
    "ai_rank": "الترتيب في الشاغر", "ai_assessment": "رابط تقييم المتقدم", "ai_evaluated_on": "وقت التقييم", "ai_stale": "النتيجة قديمة",
    "ai_duplicate_of": "الطلب الأصلي لو ده مكرر", "ai_cv_note": "ملاحظة عن ملف السيرة", "ai_flags": "الوسوم من المحرك",
    "ai_candidate_ref": "رقم المتقدم في المحرك", "ai_data_hash": "بصمة البيانات لكشف التعديل", "ai_cv_sha": "بصمة ملف السيرة",
    "ai_decision_reason": "سبب قرار الموارد البشرية", "ai_decided_by": "صاحب القرار", "ai_decided_on": "وقت القرار",
}

ENDPOINT = {
    "frappe:i_am_hr": "بيرد هل المستخدم الحالي من الموارد البشرية",
    "engine:GET /v1/candidates/{ref}": "بيرجّع بيانات متقدم واحد في المحرك",
    "engine:DELETE /v1/candidates/{ref}/cv": "بيمسح سيرة متقدم من المحرك",
}

SETTING_FRAPPE = {
    "enabled": "تشغيل الفرز الذكي على الموقع كله", "auto_screen_on_apply": "التقييم تلقائي بعد التقديم", "engine_url": "رابط المحرك",
    "api_key": "مفتاح المحرك، في حقل كلمة سر", "request_timeout": "مهلة طلبات المحرك", "callback_url": "رابط استقبال النتائج",
    "callback_secret": "سر توقيع النتائج", "id_token_secret": "سر بصمة الهوية", "provider": "مزوّد الذكاء محلي ولا سحابي", "model": "اسم النموذج اللغوي",
    "judge_prompt": "نسخة تعليمات الحكم", "ocr_provider": "مزوّد القراءة الضوئية", "timeout": "مهلة النموذج اللغوي", "max_retries": "عدد المحاولات",
    "last_synced": "آخر مزامنة مع المحرك", "allowed_facts": "الحقائق المسموح إرسالها للمحرك", "retention_days": "مدة الاحتفاظ بالأيام",
    "consent_version": "نسخة نص الموافقة الحالية", "consent_text": "نص الموافقة اللي بيظهر للمتقدم",
}

ENV = {
    "APP_ENV": "بيئة التشغيل", "LOG_LEVEL": "مستوى السجلات", "TZ": "المنطقة الزمنية للحاويات", "API_PORT": "منفذ المحرك",
    "API_BIND_TAILSCALE": "عنوان الشبكة الخاصة للمحرك", "DB_HOST_PORT": "منفذ قاعدة البيانات على السيرفر", "REDIS_HOST_PORT": "منفذ الطابور على السيرفر",
    "POSTGRES_USER": "مستخدم قاعدة البيانات", "POSTGRES_PASSWORD": "كلمة سر قاعدة البيانات", "POSTGRES_DB": "اسم قاعدة البيانات",
    "REDIS_PASSWORD": "كلمة سر الطابور", "TENANT_API_KEY": "مفتاح النظام المضيف", "CALLBACK_SECRET": "سر توقيع النتائج", "DATABASE_URL": "رابط قاعدة البيانات",
    "REDIS_URL": "رابط الطابور", "QUEUE_MODE": "طريقة تشغيل الطابور", "AI_PROVIDER": "مزوّد الذكاء الافتراضي", "LLM_BASE_URL": "رابط النموذج اللغوي",
    "LLM_MODEL": "اسم النموذج اللغوي", "VLLM_MODEL": "النموذج اللي بيتحمّل على كرت الشاشة", "VLLM_IMAGE_TAG": "نسخة خادم النموذج",
    "VLLM_MAX_MODEL_LEN": "أقصى طول نص للنموذج", "VLLM_MAX_NUM_SEQS": "أقصى طلبات متزامنة للنموذج", "LLM_TIMEOUT_S": "مهلة النموذج بالثواني",
    "LLM_MAX_RETRIES": "محاولات النموذج", "VLLM_GPU_MEMORY_UTILIZATION": "نصيبنا من ذاكرة كرت الشاشة", "CLOUD_LLM_BASE_URL": "رابط المزوّد السحابي",
    "CLOUD_LLM_MODEL": "نموذج المزوّد السحابي", "CLOUD_LLM_API_KEY": "مفتاح المزوّد السحابي", "OCR_PROVIDER": "مزوّد القراءة الضوئية",
    "OCR_THREADS": "عدد خيوط القراءة الضوئية", "MAX_UPLOAD_MB": "أقصى حجم للملف", "OCR_MIN_CONFIDENCE": "أقل ثقة مقبولة للقراءة",
    "EMBEDDING_MODEL": "نموذج بنك المتقدمين", "EMBEDDING_PROVIDER": "مزوّد بنك المتقدمين", "EMBEDDING_BASE_URL": "رابط خدمة بنك المتقدمين",
    "FILE_STORE": "مكان حفظ الملفات", "RETENTION_DAYS_DEFAULT": "مدة الاحتفاظ الافتراضية", "MAX_ATTEMPTS": "محاولات المعالجة",
    "TENANT_NAME": "اسم النظام المضيف", "ALLOWED_FACTS": "الحقائق المسموحة افتراضيًا", "CONSOLE_USER": "مستخدم الكونسول",
    "CONSOLE_PASSWORD": "كلمة سر الكونسول", "CONSOLE_SESSION_SECRET": "سر جلسة الكونسول", "CONSOLE_ID_TOKEN_SECRET": "سر بصمة الهوية في الكونسول",
    "CALLBACK_URL": "رابط النتائج الافتراضي",
}

DEV_ENV = {
    "DB_ROOT_PASSWORD": "كلمة سر قاعدة البيانات المحلية", "ADMIN_PASSWORD": "كلمة سر مدير الموقع", "TAILSCALE_IP": "عنوان الشبكة الخاصة",
    "SITE": "اسم موقع الديمو", "HR_MANAGER_PASSWORD": "كلمة سر مدير الموارد البشرية", "HR_USER_PASSWORD": "كلمة سر أخصائي التوظيف",
    "EMPLOYEE_PASSWORD": "كلمة سر الموظف", "INTERVIEWER_PASSWORD": "كلمة سر المقابِل", "ESS_PASSWORD": "كلمة سر الخدمة الذاتية",
    "SYSTEM_MANAGER_PASSWORD": "كلمة سر مدير النظام", "PORTAL_PASSWORD": "كلمة سر المتقدم صاحب الحساب",
}

COMMAND = {
    "make:builder-check": "بيتأكد إن البناء على المُنشئ الافتراضي بس", "make:build": "بيبني صور المحرك", "make:env": "بيعمل ملف الإعدادات بأسرار عشوائية",
    "make:install": "بيثبّت مكتبات المحرك محليًا", "make:test": "بيشغّل اختبارات المحرك", "make:lint": "بيفحص تنسيق الكود", "make:fmt": "بيظبط تنسيق الكود",
    "make:typecheck": "بيفحص الأنواع في الكود", "make:up": "بيشغّل خدمات المحرك", "make:down": "بيوقّف خدمات المحرك", "make:logs": "بيعرض سجلات المحرك",
    "make:llm-logs": "بيعرض سجلات النموذج اللغوي", "make:gpu": "بيعرض استهلاك كرت الشاشة", "make:ps": "بيعرض حالة الخدمات", "make:migrate": "بيحدّث جداول قاعدة البيانات",
    "make:revision": "بيعمل تحديث جديد للجداول", "make:seed": "بيحط بيانات الديمو في المحرك", "make:cvs": "بيعمل السير الذاتية الوهمية", "make:receiver": "بيشغّل مستقبل نتائج للتجربة",
}

SCRIPT = {
    "callback_receiver.py": "مستقبل نتائج صغير للتجربة", "cv_texts.py": "نصوص السير الوهمية", "init_env.py": "إنشاء ملف إعدادات المحرك", "make_cvs.py": "توليد ملفات السير الوهمية",
    "seed.py": "تحميل بيانات الديمو في المحرك", "seed_data.py": "بيانات الديمو", "compose.sh": "تشغيل الحاويات بالمُنشئ الافتراضي",
    "clean_install.sh": "تجربة التثبيت النظيف على نسخة منفصلة", "init_env.sh": "إنشاء ملف إعدادات النسخة المحلية", "reset_demo.sh": "ترجيع الديمو لأوله",
    "setup.sh": "تجهيز النسخة المحلية من Frappe", "start.sh": "تشغيل النسخة المحلية واسترجاع قاعدة البيانات", "acceptance.py": "اختبارات القبول في المتصفح",
    "apply_via_form.py": "تقديم طلب من النموذج زي المتقدم", "design_audit.py": "فحص التصميم على كل المقاسات", "design_pairs.py": "صور قبل وبعد",
    "desk_shots.py": "صور شاشات Frappe", "frappe_ui.py": "أداة تحكم قديمة في المتصفح", "full_test.py": "الاختبار الشامل في المتصفح", "pw.py": "أدوات المتصفح المشتركة",
    "test_report.py": "كتابة تقرير الاختبار", "walkthrough_shots.py": "صور الجولة", "facts.py": "جمع الأرقام الحقيقية للدليل", "inv.py": "أرقام بنود الجرد",
    "inventory.py": "جرد كل حاجة من الكود", "lint_ar.py": "فحص قواعد الكتابة", "model.py": "بنية محتوى الدليل", "render_docx.py": "إخراج نسخة Word",
    "render_html.py": "إخراج نسخة PDF", "shots.py": "صور الدليل", "seed_demo.py": "تجهيز الديمو في Frappe", "submit_demo_applications.py": "تقديم الخمسة وعشرين متقدم",
    "bench.py": "قياس السرعة", "make_gold.py": "توليد مجموعة الاختبار الذهبية", "run.py": "تشغيل التقييم على المجموعة الذهبية", "build.py": "بناء الدليل كله",
    "coverage_check.py": "مقارنة الجرد بالكود", "explain.py": "شرح بنود الملحق", "ch_intro.py": "فصول البداية", "ch_journey.py": "فصل الرحلة",
    "ch_stages.py": "فصل المراحل", "ch_score.py": "فصل الدرجة", "ch_cases.py": "فصل الحالات", "ch_rest.py": "الفصول الأخيرة", "ch_appendix.py": "الملحق",
    "docshots.py": "صور الأوامر والمستندات",
}

BENCH = {
    "bench get-app": "تنزيل التطبيق من مستودعه", "bench --site <site> install-app ido_talent_ai": "تثبيت التطبيق على الموقع",
    "bench --site <site> migrate": "تحديث الموقع بعد التثبيت أو التحديث", "bench --site <site> run-tests --app ido_talent_ai": "تشغيل اختبارات التطبيق",
    "bench --site <site> uninstall-app ido_talent_ai": "إزالة التطبيق وترجيع الموقع زي ما كان",
}

HOOK = {
    "ido_talent_ai.screening.on_applicant_insert": "بعد حفظ الطلب: بيجهّز التقييم ويشغّله بعد الحفظ",
}

SECURITY = {}

ARCH = {
    "service:db": "قاعدة بيانات المحرك", "service:redis": "طابور المهام", "service:api": "واجهة المحرك والكونسول", "service:worker": "عمّال المعالجة",
    "service:vllm": "خادم النموذج اللغوي على كرت الشاشة", "service:embed": "خدمة بنك المتقدمين على المعالج", "dev-service:mariadb": "قاعدة البيانات المحلية لـ Frappe",
    "dev-service:redis-cache": "الذاكرة المؤقتة لـ Frappe", "dev-service:redis-queue": "طابور Frappe", "dev-service:bench": "النسخة المحلية من Frappe",
    "repo:talent-ai": "مستودع المحرك والوثائق", "repo:ido_talent_ai": "مستودع تطبيق Frappe", "install": "خطوات التثبيت على المنصة",
    "uninstall": "الإزالة بترجّع المنصة زي ما كانت", "in-memory-db": "قاعدة البيانات المحلية في الذاكرة للاختبار بس", "builder": "البناء بالمُنشئ الافتراضي بس",
    "gpu-cap": "سقف 40% من كرت الشاشة",
}

EVAL = {
    "run:8B v2": "تجربة نفس النموذج بتعليمات عربي، وطلعت أضعف", "run:4B v1": "تجربة نموذج أصغر، وطلع أضعف في النصوص",
    "throughput:2": "السرعة بعاملين", "quote-ratio": "شرط مطابقة الاقتباس 90% بعد توحيد الحروف",
}

DECISION_AR = {
    "claude:1": "إجابات النموذج هي المصدر الأساسي، والسيرة اختيارية", "claude:10": "الأسماء من وثيقة متطلبات العميل",
    "claude:14": "السيرة غير المقروءة عمرها ما بتفشّل التقييم", "progress:Old-application demo case": "حالة طلب قديم في الديمو لمدة الاحتفاظ",
    "progress:Fonts bundled in the app": "الخط جوه التطبيق بدل خدمة برّه", "progress:English stage notes are stored next to the Arabic ones": "ملاحظات المراحل بالإنجليزي جنب العربي",
    "progress:Synthetic Employee records for the demo users": "سجلات موظفين وهمية لمستخدمي الديمو اللي محتاجين دور موظف",
    "progress:A CV problem never fails a screening": "أي مشكلة في ملف السيرة عمرها ما بتفشّل التقييم",
    "progress:«إعادة تقييم الكل» skips applicants without consent": "«إعادة تقييم الكل» بتعدّي اللي سحبوا الموافقة وبتقول عددهم",
    "progress:Screenshots cut to the part the page explains": "الصورة الطويلة بيظهر أولها بس، عشان تتقري بعرض الصفحة",
    "progress:Page numbers read from the printed PDF": "أرقام صفحات الفهرس مقروءة من النسخة المطبوعة نفسها",
    "progress:The Word file is checked through LibreOffice": "نسخة الوورد اتراجعت صفحة صفحة بعد تحويلها بـ LibreOffice",
}


def explain(it: dict) -> str:
    cat, key = it["cat"], it["id"].split(":", 1)[1]
    if cat == "doctype":
        return DOCTYPE.get(key, "نوع بيانات من التطبيق")
    if cat == "field":
        return FIELD.get(key.split(".", 1)[1], "حقل أضافه التطبيق")
    if cat == "endpoint":
        if key in ENDPOINT:
            return ENDPOINT[key]
        return "طريق في الواجهة البرمجية" + (" لأي حد" if it.get("guest") else "")
    if cat == "setting":
        kind, name = key.split(":", 1)
        if kind == "frappe":
            return SETTING_FRAPPE.get(name, "إعداد في شاشة الإعدادات")
        if kind == "engine-env":
            return ENV.get(name, "إعداد في ملف المحرك")
        if kind == "dev-env":
            return DEV_ENV.get(name, "إعداد النسخة المحلية")
        return "حد الطلبات من نفس الجهاز في عشر دقايق"
    if cat == "command":
        if key.startswith("make:"):
            return COMMAND.get(key, "أمر في المحرك")
        if key.startswith("bench:"):
            return BENCH.get(key[6:], "أمر Frappe")
        return SCRIPT.get(key.rsplit("/", 1)[-1], "سكربت مساعد")
    if cat == "hook":
        return HOOK.get(key, "خطوة تلقائية بيشغّلها Frappe")
    if cat == "architecture":
        return ARCH.get(key, "جزء من البنية")
    if cat == "evaluation":
        return EVAL.get(key, "نتيجة من تقرير التقييم")
    if cat == "decision":
        if key in DECISION_AR:
            return DECISION_AR[key]
        if key.startswith("open:"):
            return "سؤال مفتوح أو قرار مسجّل في ملف الأسئلة"
        if key.startswith("claude:"):
            return "قرار ثابت من قرارات المشروع"
        return "قرار اتاخد أثناء الشغل ومكتوب سببه"
    if cat in ("stage", "flag", "status"):
        return it.get("label_ar") or "حالة من حالات المعالجة"
    if cat == "role":
        return "مستخدم تجريبي أو دور في Frappe"
    if cat == "button":
        return f"زرار «{it['label_ar']}»" if it.get("label_ar") else "زرار أو إجراء في الشاشة"
    if cat == "screen":
        return "شاشة من شاشات النظام"
    if cat == "security":
        return SECURITY.get(key, "إجراء أمان")
    return "بند من الجرد"
