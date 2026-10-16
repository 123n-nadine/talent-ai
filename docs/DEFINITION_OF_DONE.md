# Definition of done — the demo and the guide as a real system in Frappe

Reference: `reference/demo/talent-ai-demo.html` (tour steps 0–15) and `reference/guide/talent-ai-workflow.pdf` (steps 0–15 and their «تكملة» pages). Target: the local Frappe bench in `dev-frappe/` (Frappe 16.31.0, ERPNext 16.32.x, HRMS develop) with the app `ido_talent_ai` and the engine `talent-engine`. Everything real: no simulation, no fixed data.

Client features (requirements document §5): **01** job criteria · **02** reading the application · **03** screening and matching · **04** ranking · **05** HR review and decision · **10** candidate comparison · **13** talent pool. Postponed and never built: 06, 07, 08, 09, 11, 12, 14.

Status: ⬜ not started · 🔶 built, evidence pending (phase 7/8) · ✅ done and tested · ❌ not done (reason given).

Last update: 2026-10-16, end of phase 8 — everything done (details in `docs/PROGRESS.md`; evidence in `docs/ACCEPTANCE_REPORT.md`; tour in `docs/WALKTHROUGH.md`).

## 1. Demo steps and guide continuations

| # | Step (demo / guide) | Where in Frappe | Feature | How it is tested | Status |
|---|---|---|---|---|---|
| 0 | خريطة الدورة — cycle map | Workspace **Talent AI** (`/desk/talent-ai`): the cycle as clickable cards (profile → opening → portal → form → processing → applicants → ranking → pool → jobs → settings → audit) with who acts at each stage | — | Open the workspace as HR Manager; every card opens the real screen | ✅ |
| 1 | ملف المعايير — AI Job Profile | DocType **AI Job Profile** (+ child tables AI Job Criterion, AI Job Rule, AI Job Question), linked to the Job Opening; buttons «اقتراح معايير AI», «نسخ من قالب المسمى الوظيفي», «معاينة الأثر», «اعتماد» | 01 | Create the «مشرف أمن — الرياض» profile from the template; weights 30/20/15/15/8/7/5 | ✅ |
| 1+ | تكملة: سُلّم التقييم والأوزان ومعاينة الأثر | Same form: rubric 0/25/50/75/100 per criterion, total-weight indicator, approval blocked unless 100% (server-side), impact preview dialog (who moves, old → new score/band/rank) before approval, versions v1, v2… | 01 | Set a weight so the total is 105 → «اعتماد» refused by the server; change 15→20 and 15→10 → impact preview lists the movers; approve → v2 and old assessments become stale | ✅ |
| 2 | الشاغر — Job Opening | Job Opening custom fields `ai_enabled`, `ai_profile`, `ai_profile_approved` (read-only), `job_application_route` set to the AI form, public link | 01 | Enable AI on the opening; `ai_profile_approved` follows the profile approval | ✅ |
| 3 | النشر — public portal | HRMS `/jobs` portal (Arabic, RTL) listing published openings | 02 | Open `/jobs` as Guest | ✅ |
| 4 | صفحة الوظيفة — job page | HRMS job page `/jobs/<company>/<route>` with description; «قدّم الآن» goes to the AI form; eligibility requirements shown as Arabic sentences | 02 | Open the job page as Guest; the button leads to the AI form with the opening | ✅ |
| 5 | نموذج التقديم — application form | Public page `/ai-apply/new?job_title=<opening>` (Arabic RTL): applicant data, facts the rules need, CV optional (PDF/DOCX/JPG/PNG), consent required, creates a **Job Applicant** linked to the opening with every answer in the child table **AI Applicant Answer** | 02 | Submit as Guest with and without CV; the Job Applicant exists immediately with all answers | ✅ |
| 5+ | تكملة: أسئلة الفرز في نموذج التقديم | Questions rendered from the approved AI Job Profile; height/weight only when the opening has those rules; hint «اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب» under numeric questions; blank ≠ 0 kept end to end | 02 | Opening without height rule → no height field; leave one answer blank and write 0 in another → blank shows «لم يُجب», 0 is a real answer | ✅ |
| 6 | المعالجة — the 10 stages | Automatic: `after_insert` → **AI Recruitment Job** → engine `POST /v1/screenings` → HMAC callback → **AI Candidate Assessment**. On the Job Applicant form: the 10 stages with timings, CV analysis (original file, OCR boxes coloured by confidence, extracted text, before/after redaction, evidence highlighted in text and image), live status without manual refresh | 02, 03 | Submit from the public form and watch `ai_status` go Processing → Completed / Needs Review on the open form; open the CV analysis of a scanned CV | ✅ |
| 7 | دفعة الألف — batch | Page **AI Batch Monitor** (`/desk/ai-batch`) per opening: queued / processing / completed / needs review / failed counts and throughput from the real AI Recruitment Jobs (no simulation) | 03 | Submit the 25 seed applications and watch the counters move | ✅ |
| 8 | قائمة المتقدمين — Job Applicant list | Job Applicant list view: columns and standard filters `ai_status`, `ai_score`, `ai_band`, `ai_eligibility`, `job_title`; duplicate indicator; sort by score | 04 | Filter by opening and band; sort by score | ✅ |
| 9 | شاشة المتقدم — Job Applicant form | Section «تقييم الذكاء الاصطناعي»: eligibility, score, band, coverage, rank, summary, criteria with level and evidence («إجابة النموذج» / «من السيرة» / «تؤكده السيرة»), CV panel; buttons ترشيح / تعليق / رفض with reason and decision maker; «إلغاء حكم الذكاء» per criterion with mandatory reason; the AI never changes the status | 03, 05 | Open HR-APP for Sultan: 81.5, evidence per criterion, quote highlighted; reject without reason refused; with reason → status changes and is logged | ✅ |
| 9+a | تكملة: نقاط القوة والنواقص وما يرفع الدرجة | Same section: strengths (75–100), gaps (0–25 or missing), «ما الذي يرفع درجته» with exact points | 03 | Sultan: +7 for first aid | ✅ |
| 9+b | تكملة: التعارض بين الإجابة والسيرة | Same section: answer vs CV side by side, lower level used, Needs Review | 03 | Seed applicant whose CV states fewer years than the answer | ✅ |
| 9+c | تكملة: الطلب المكرر | Same section: duplicate banner linking the original (same national-ID HMAC), not ranked, nothing deleted | 03, 04 | Submit the same person twice from the form | ✅ |
| 9+d | تكملة: النتائج القديمة وإعادة التقييم | Banner «النتيجة لا تعكس آخر تعديل» after editing answers/facts, «قديم» after a new profile version; button «إعادة التقييم» (one) and «إعادة تقييم الكل» (opening) | 03 | Edit an answer → banner and out of ranking; re-score → back | ✅ |
| 10 | الترتيب — ranking | Page **AI Ranking** (`/desk/ai-ranking`) per opening: completed + eligible + current only, collapsed groups with reasons (غير مستوفٍ، يحتاج مراجعة، جاري، فشل، قديم، مكرر), approved weights, how it is computed | 04 | Ranking for the seeded opening matches the scores; groups list the excluded with reasons | ✅ |
| 10+ | تكملة: تصدير القائمة | CSV export UTF-8 with BOM from the ranking page | 04 | Open the CSV in Excel/LibreOffice: Arabic correct | ✅ |
| 10c | المقارنة — comparison | Ranking page: select 2–3 applicants → side-by-side table criterion by criterion with level, evidence and incomplete results marked | 10 | Compare 3 ranked applicants; a needs-review applicant shows «غير مكتمل» | ✅ |
| 11 | بنك المتقدمين — talent pool | Page **AI Talent Pool** (`/desk/ai-talent-pool`) from a Job Opening: hard rules first, then semantic similarity (embeddings), excluded section (consent withdrawn, retention expired, already applied/hired), «اقتراح فقط» | 13 | Pool search for a new opening; an applicant with withdrawn consent and one with expired retention appear only in the excluded section | ✅ |
| 12 | مهام الذكاء — AI Recruitment Job | DocType **AI Recruitment Job** list/form: type, reference, status, attempts, error, engine screening id, «إعادة المحاولة» | 03 | Every application has its job; counts match | ✅ |
| 12+ | تكملة: الفشل وإعادة المحاولة | Engine down → application saved, job retried with backoff, then Failed with a clear error; «إعادة المحاولة» works when the engine is back; hourly scheduler retries | 03 | Stop the engine API, submit, see Failed; start it, retry → Completed | ✅ |
| 13 | الإعدادات — AI Recruitment Settings | Single DocType: enabled, engine URL, API key, callback secret, ID-token secret, auto-screen; provider / model / OCR / timeout / max retries read from and written to the engine (`/v1/settings`); allowed facts | 01 | Change max retries in Frappe → visible in the engine settings | ✅ |
| 14 | سجل التدقيق — AI Recruitment Audit Log | DocType (read-only, append-only): time, applicant, opening, action, user, reason, profile version | 05 | Every job, override and decision appears with user and reason | ✅ |
| 15 | اختبارات القبول — acceptance tests | `docs/ACCEPTANCE_REPORT.md` with the client's 8 criteria, result and evidence (screenshots, logs) | all | See §3 | ✅ |

## 2. Required capabilities (Nadine's list, 2026-10-15)

| # | Requirement | Covered by | Status |
|---|---|---|---|
| R1 | AI Job Profile: rubric 0/25/50/75/100, weights 100% or approval blocked, rules, questions, impact preview, «اقتراح معايير AI» as draft, «نسخ من قالب المسمى الوظيفي», versions | steps 1, 1+ | ✅ |
| R2 | Job Opening: `ai_enabled`, `ai_profile`, `ai_profile_approved` | step 2 | ✅ |
| R3 | Public site: jobs page, job page, Arabic form, questions from the profile, height/weight only when ruled, the 0-vs-blank hint, CV optional, consent required | steps 3, 4, 5, 5+ | ✅ |
| R4 | Automatic: application saved even when the engine is down; `ai_status` Processing → Completed / Needs Review / Failed, updated on the page without manual refresh | steps 6, 12+ | ✅ |
| R5 | Applicant page: 10 stages with timings, CV analysis, score/band/coverage/rank, evidence types, strengths/gaps/raise, contradiction, duplicate, stale + re-score, override with reason, Shortlist/Hold/Reject with reason and decision maker, AI never changes status | steps 6, 9, 9+a–d | ✅ |
| R6 | Applicant list: columns and filters `ai_status`, score, band, eligibility, opening | step 8 | ✅ |
| R7 | Batch monitor per opening with real counts | step 7 | ✅ |
| R8 | Ranking per opening: ranked only completed + eligible, grouped others with reasons, CSV (Arabic, Excel), comparison of 2–3 (feature 10) | steps 10, 10+, 10c | ✅ |
| R9 | Talent pool from the opening (feature 13): rules first, then similarity, excludes withdrawn consent and expired retention, «اقتراح فقط» | step 11 | ✅ |
| R10 | AI Recruitment Job with attempts, error and retry; AI Recruitment Settings; AI Recruitment Audit Log | steps 12, 12+, 13, 14 | ✅ |
| R11 | «الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة» wherever a score appears | all score screens | ✅ |
| R12 | Arabic RTL everywhere; only HR Manager and HR User see the AI section | all screens + permission tests | ✅ |
| C1 | Talent Console stays a standalone engine test tool, plus a CV analysis screen and a «جرّب ملف» page | console | ✅ |
| S1 | Seed: opening «مشرف أمن — الرياض» with the approved profile and 25 fictional applicants submitted through the public form itself (image, PDF, Word and no CV; not eligible, needs review, contradiction, duplicate) | `ido_talent_ai/scripts/seed_demo.py` | ✅ |

## 3. Client acceptance criteria (definition of done, phase 1)

| # | Criterion (client's words) | Proof | Status |
|---|---|---|---|
| A1 | عند تقديم طلب من Web Form، يظهر Job Applicant مرتبطًا بالوظيفة وبجميع الإجابات | Submit from the public form; Job Applicant with `job_title` and every AI Applicant Answer row; automated Frappe test | ✅ |
| A2 | عند تفعيل AI، تظهر حالة Processing ثم Completed أو Needs Review أو Failed بوضوح | Screenshots of each status; automated test of the callback | ✅ |
| A3 | كل درجة لها سبب ودليل من بيانات المتقدم، ولا تظهر مهارات لم يذكرها | 100% of levels > 0 carry verified evidence (engine check + gold set) | ✅ |
| A4 | عند تعديل بيانات المتقدم، لا تبقى النتيجة القديمة وكأنها حديثة | Edit an answer → stale banner, out of ranking | ✅ |
| A5 | قائمة المرشحين لا تخلط بين الوظائف، وقرار التوظيف لا يتغير دون مستخدم مخوّل | Two openings ranked separately; Employee user cannot change status or see the AI section; AI never writes `status` | ✅ |
| A6 | عند تعطل خدمة AI، يظل تقديم الطلب يعمل بشكل طبيعي | Engine stopped → application saved, job Failed, retry later | ✅ |
| A7 | المقابلات والاختبارات والعروض تستخدم بيانات المرشح نفسه | Not applicable in phase 1 (features postponed); recorded as such | n/a (postponed features, decision 11) |
| A8 | تظهر الشاشات العربية بشكل صحيح، مع احترام صلاحيات كل مستخدم | Screenshots in Arabic; role tests (HR Manager, HR User, Employee) | ✅ |

## 4. Delivery

| Item | Status |
|---|---|
| `docs/WALKTHROUGH.md` (Egyptian Arabic, guide order, screenshots in `docs/screenshots/`) | ✅ |
| `docs/ACCEPTANCE_REPORT.md` | ✅ |
| Clean install on a fresh bench + site (`bench get-app` → `install-app` → `migrate`) and clean uninstall | ✅ |
| `docs/DEPLOY.md` filled from `DEPLOY_CHECKLIST.md` | ✅ |

## 5. Round 2 (Nadine, 2026-10-16 night)

| # | Item | Where | Status |
|---|---|---|---|
| H1 | Home page «التوظيف الذكي» shown first to HR after login: nine big buttons in order (ملف المعايير، الشواغر، صفحة التقديم العامة، قائمة المتقدمين، الترتيب، بنك المتقدمين، مهام الذكاء، الإعدادات، سجل التدقيق) with one line each; Arabic by default for HR users | page `ai-recruitment`, hook `on_session_creation`, first sidebar item | ✅ |
| H2 | Decisions: dev-frappe scripts in git without `.env`; status reason stays audit-only; only the default Docker builder; the in-memory Frappe DB is for testing only | `.gitignore`, `dev-frappe/`, `Makefile` (`builder-check`), `scripts/compose.sh`, `DEPLOY.md`, `CLAUDE.md`, `OPEN_QUESTIONS.md` | ✅ |
| H3 | Permanent test that an application is always saved (queue down, hook crash, audit down, DB conflict, AI off, damaged CV) | `test_application_is_always_saved` + retried save in `api.apply` | ✅ |
| D1 | Design pass on every screen (1366/1440/1920, mobile for the public pages), RTL, font, colours with a fixed meaning | Frappe, console, public site, form; `tools/ui/design_audit.py`: 10,487 layout/contrast issues → 2 (the HRMS sticky mobile button), 0 JS errors on 110 screens | ✅ |
| T1 | Full browser test of the whole system (users, CV types, cases, timings), bugs fixed with tests, `docs/TEST_REPORT.md` | `tools/ui/full_test.py` → `docs/TEST_REPORT.md`: 38 of 38 checks after the fixes (F1 RTF CV, F2 re-score all), demo restored with `reset_demo.sh` | ✅ |
| T2 | Roles and permissions test (every recruitment role, every screen, screenshots of the refusals) | `TEST_REPORT.md` §2: 9 kinds of user × 16 screens + 14 server calls; Employee, Interviewer, self-service, website user and guest never see a score, an assessment or a CV | ✅ |
| G1 | Inventory from the code (`docs/guide/COVERAGE.md`) and a check script with zero missing | `tools/guide/inventory.py` → 558 items (screens, buttons, DocTypes, fields, endpoints, hooks, stages, flags, statuses, settings, roles, commands, decisions, evaluation, security, architecture), each with its guide page, screenshot and test; `tools/guide/coverage_check.py` → MISSING 0 | ✅ |
| G2 | Full guide in Egyptian Arabic, PDF (Chromium) and Word | `docs/guide/talent-ai-full-guide.pdf` (123 pages) and `.docx` (123 pages through LibreOffice); writing rules and page layout checked by code, every page looked at as an image, index of terms and screens at the end | ✅ |

## 6. Round 3: consent defaults (Nadine, 2026-10-16; until the client confirms)

| # | Item | Where | Status |
|---|---|---|---|
| C1 | #20: a paper application without consent is saved but never screened («بانتظار الموافقة»); HR records the consent with a mandatory source; who and when are kept; the screening starts by itself | `api.record_consent`, `screening.on_applicant_insert`, ranking group `awaiting_consent`, Frappe `test_paper_application_waits_until_hr_records_the_consent`, browser K16 | ✅ |
| C2 | #21: a withdrawal takes the applicant out of the ranking at once into «مستبعد: سحب الموافقة» with no score and no details; the engine erases documents and files, profile, index and results; Frappe keeps the application only | engine `candidates.erase_ai_data`, ranking group `consent_withdrawn`, `tests/test_consent.py`, Frappe withdrawal tests, browser K17 | ✅ |
| C3 | Both written in `OPEN_QUESTIONS.md` as defaults until the client confirms | #20, #21 | ✅ |
| C4 | `make install` runs `uv sync --group documents` | `talent-engine/Makefile`, README | ✅ |
| C5 | The guide pages of both cases updated in the PDF and the Word file | chapter 9 (cases 9 أ–هـ and 10 أ–ب, seven pages with their screenshots), privacy, FAQ, open questions, glossary, fixed bugs; PDF and Word 130 pages each, 0 page problems; inventory 576 items, MISSING 0 | ✅ |
