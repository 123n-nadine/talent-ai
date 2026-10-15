# Talent AI v2 — clickable prototype (نموذج تجريبي)

`talent-ai-demo.html` is one self-contained file (HTML + CSS + vanilla JS). Double-click it to open; no server, no build step, no backend. The only network request is the Google Font *IBM Plex Sans Arabic* (a system font is used if offline).

All data is fictional: company "شركة الحراسة الوطنية (بيانات وهمية)", invented names, masked IDs. Nothing is sent anywhere; "uploads" keep only the file name.

## What changed in v2 (client requirements document)

- **Form answers are the primary source; the CV is optional.** Each *AI Job Profile* defines screening questions that appear in the public form. Evidence is either «إجابة النموذج» (field + value) or «من السيرة» (literal quote). A blank answer is «لم يُجب» (missing evidence, counts in coverage); «0» is a real answer.
- **New scoring model.** Weights are percentages totalling 100 % (approval is blocked otherwise). Each criterion is judged on fixed levels 0 / 25 / 50 / 75 / 100 with a written rubric. `score = Σ(weight% × level) ÷ 100`; missing evidence → level 0 flagged «دليل ناقص»; coverage = share of weight with evidence; bands high ≥ 75 / medium 50–74 / low < 50; a mandatory criterion at 0 → low; coverage < 60 % → needs review.
- **Client names.** DocTypes *AI Recruitment Settings*, *AI Job Profile* (linked to the Job Opening, with «نسخ من قالب المسمى الوظيفي» and a version), *AI Job Criterion*, *AI Candidate Assessment*, *AI Assessment Evidence*, *AI Recruitment Job*, *AI Recruitment Audit Log*; fields `ai_enabled`, `ai_profile`, `ai_profile_approved` on Job Opening and `ai_status`, `ai_score`, `ai_assessment`, `ai_evaluated_on` on Job Applicant. Our additions (screening questions, eligibility rules, `mandatory` + rubric, `source`, `attempts`, `engine_url`) are marked «إضافة مقترحة» in developer view.
- **Processing status and jobs.** `ai_status` (Processing / Completed / Needs Review / Failed) everywhere; a new «مهام الذكاء الاصطناعي» screen with attempts, errors and «إعادة المحاولة». One applicant has a corrupt CV → job Failed after 3 attempts; the application itself is saved and visible.
- **Criteria versions and stale results.** Editing a weight makes a draft; approving creates v4 and flags every v3 assessment «قديم»; «إعادة تقييم الكل» queues jobs. Editing an answer flags «النتيجة لا تعكس آخر تعديل». Stale results are never ranked.
- **Talent pool** also excludes withdrawn consent and expired retention (collapsed section with reasons).
- **Extras:** strengths / gaps / «ما الذي يرفع درجته» with exact points; answer-vs-CV contradiction (lower value used, needs review); duplicate applications (same national ID, linked, nothing deleted); batch view «دفعة الألف متقدم» (simulation, illustrative numbers); impact preview before approval; CSV export (UTF-8 with BOM); acceptance-tests screen with the client's 8 criteria checked live.
- Not included on purpose (postponed): interview questions, voice interview, technical assessments, interview summary, job-offer draft, applicant status portal, recruitment dashboard.

Header controls: **عربي / EN** (labels + direction), **جولة موجّهة / تصفح حر**, **عرض المطوّر** (DocType fields, endpoints, JSON per screen), **بيانات تجريبية** badge.

## 5-minute presentation click path

Open the file in Arabic (default) and keep **جولة موجّهة** on. Use **التالي** to advance (steps 0–15).

1. **0 — خريطة الدورة** (15 s): who acts at each stage; side branches بنك المتقدمين · مهام الذكاء · اختبارات القبول.
2. **1 — ملف المعايير** (50 s): rubric table with weights (total chip «المجموع: 100%»), hard rules, screening questions. Change «إدارة الورديات» 15 → 20: the chip turns red and **اعتماد** is disabled until the total is 100 again (set «رخصة» 15 → 10). Click **معاينة الأثر** to see bands and who moves before approving. Optional: **مسودة بالذكاء الاصطناعي**.
3. **2 — الشاغر** (15 s): `ai_enabled`, `ai_profile`, `ai_profile_approved`, the public link.
4. **3 → 4 → 5 — الموقع العام** (60 s): portal → job page → form. Point at «أسئلة الفرز» (from the profile), «اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب», and «السيرة الذاتية (اختياري)». Developer view shows the payload: answers + facts, no name/ID/photo. Tick the consent and **إرسال الطلب** (no CV needed).
5. **6 — المعالجة** (90 s): pipeline for the applicant just created. Stages: استلام → قراءة إجابات النموذج → استخراج نص السيرة → إخفاء الهوية → الملف المنظّم → التحقق من الأدلة → الشروط الإلزامية → الحكم على المعايير → الدرجة والترتيب → الفهرسة. With no CV the three CV stages show «لا توجد سيرة — التقييم من الإجابات فقط». Pick **سلطان الحربي — صورة ممسوحة** for OCR; pick **محمد الشهري** to see the contradiction flagged at stage 6. Stage 8 shows the level and rubric per criterion; stage 9 shows the real arithmetic (`30×75 + 20×100 + … = 8150 ÷ 100 = 81.5`).
6. **7 — دفعة الألف** (20 s): **تشغيل المحاكاة**; counters and progress bar, labelled «محاكاة — الأرقام توضيحية».
7. **8 — قائمة المتقدمين** (20 s): column and filter `ai_status`; «طلب مكرر» tag on حسن القرني; Failed and Processing rows without a score.
8. **9 — شاشة المتقدم** (70 s): سلطان الحربي — levels with «إجابة النموذج» + «تؤكده السيرة», strengths/gaps and «ما الذي يرفع درجته» (+7 for first aid). Open **محمد الشهري** → «تعارض بين الإجابة والسيرة» side by side. Open **فيصل العمري** → Failed with a clear error and **إعادة المحاولة → التقييم من الإجابات فقط**. Click **تعديل** on an answer → the result is flagged «لا تعكس آخر تعديل» and leaves the ranking until **إعادة التقييم**.
9. **10 — الترتيب** (40 s): ranked list (completed + eligible only); collapsed sections for not eligible, needs review, and «غير مرتَّبين لأسباب أخرى» (processing, failed, stale, duplicate). Tick 2–3 → comparison. **تصدير القائمة CSV** downloads a UTF-8 BOM file.
10. **11 — بنك المتقدمين** (30 s): **ابحث في البنك**; hard rules first; «مستبعدون بسبب الموافقة أو مدة الاحتفاظ (2)».
11. **12 — مهام الذكاء** (20 s): the queue with attempts and the Failed job; **إعادة تقييم الكل** after approving a new profile version.
12. **13 — الإعدادات** (15 s): provider, model, enabled, timeout, max_retries, engine_url, allowed facts.
13. **14 — سجل التدقيق** (15 s): every job and HR action with the masked applicant ID and the criteria version.
14. **15 — اختبارات القبول** (20 s): **تشغيل الاختبارات** → 7 pass, test 7 «خارج نطاق المرحلة الأولى».

Optional: toggle **EN** on the applicant form, the ranking or the profile to show the English/LTR rendering.

## Worked example (سلطان الحربي)

| criterion | weight | level | w × level |
|---|---|---|---|
| خبرة الإشراف (4 سنوات) | 30 % | 75 | 2250 |
| الخبرة الأمنية (6 سنوات) | 20 % | 100 | 2000 |
| إدارة الورديات (أعدّها بنفسه) | 15 % | 100 | 1500 |
| الرخصة (سارية) | 15 % | 100 | 1500 |
| التقارير (أحيانًا) | 8 % | 50 | 400 |
| الإسعافات (لا) | 7 % | 0 | 0 |
| اللغات (العربية والإنجليزية) | 5 % | 100 | 500 |
| **total** | **100 %** | | **8150 → 81.5** |

Coverage 100 %, band مرتفعة, rank 3 of 9 after راكان الدوسري submits (3 of 8 before).

## Endpoints shown in developer view

`POST /v1/screenings` · `GET /v1/screenings/{id}` · `GET /v1/jobs/{ref}/ranking` · `POST /v1/jobs/{ref}/rescreen` · `POST /v1/talent-pool/search`, each wrapped in an *AI Recruitment Job*, with results delivered through the callback `ido_talent_ai.api.receive_result`. HR actions: `override_level`, `export_shortlist`.

## Files

- `talent-ai-demo.html` — the prototype
- `screenshots/ar_*.png` — every tour step in Arabic, `en_*.png` — three screens in English
- `README.md` — this file

## Self-check performed

`window.__selfCheck()` checks: weights sum to 100 on every approved profile and version; every level is one of 0/25/50/75/100; every stored score equals the formula; every form evidence equals its stored answer; every CV quote exists literally in the (redacted) text; blank ≠ zero; Failed / Processing / stale / duplicate never ranked; ranking sorted; duplicates linked and national IDs masked; excluded pool members never invitable; acceptance tests 1–6 and 8 pass; no text overflow. Result on 2026-10-13: 0 issues, 26 applicants, 9 ranked, 3 needs-review, 2 not-eligible, 3 excluded for «مشرف أمن — الرياض». Console: 0 errors.
