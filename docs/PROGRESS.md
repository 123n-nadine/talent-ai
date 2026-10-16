# Progress log (autonomous run from 2026-10-15)

Nadine asked for the remaining phases (5 → 8) to run without stopping, merging each phase into `main`. This file records what was done per phase and every decision taken without her, with the reason. The checklist is `docs/DEFINITION_OF_DONE.md`.

## Phase 5 (continued) — CV analysis in the console

Done (merged into `main` 2026-10-15):
- Every extraction now returns a **layout**: page sizes and one entry per text line with its box and confidence (1.0 for a PDF text layer, the recogniser score per segment for OCR). Stored on the document (migration e5c3f4a7b8c9). Word/DOC/RTF CVs get a LibreOffice PDF preview so they can be shown as pages too.
- New engine endpoints: `GET /v1/candidates/{ref}/cv?include_raw=true` (layout, before/after pairs), `GET …/cv/file` (original), `GET …/cv/pages/{n}` (page image in the layout's pixel space); `/v1/documents/inspect` returns layout and page images without storing anything; screening output maps each CV quote to its boxes (`cv.quote_boxes`).
- Console: «تحليل السيرة» (original page with boxes coloured by confidence, extracted lines with confidence, CV evidence that highlights in the text and on the page, redaction before/after) and «جرّب ملف» (same view for any uploaded file, nothing stored). Render-tested in headless Chrome for a scan, a PDF and a Word CV: no JS errors.

Decisions taken alone:
- **Redaction keeps line breaks** when collapsing repeated tokens, so the before/after view can pair lines one to one.
- **Layout in display pixels** (110 dpi for PDFs, native pixels for images): the UI scales one SVG over the page image; no client-side PDF rendering library needed.
- Known limit: redaction removes the word «السعودي» also inside «الهلال الأحمر السعودي» (nationality words are removed everywhere). Privacy-safe, sometimes loses meaning in a quote.

## Phase 6 — local Frappe with the client's versions + the app

Done (branch `phase-6-frappe` in both repos):
- **Local bench** in `dev-frappe/` (git-ignored): Frappe v16.31.0, ERPNext v16.32.0, HRMS develop pinned at 640af1592a01 (same day), Python 3.14, compose project `talentai-frappe`, ports 18050/18051 (127.0.0.1 + Tailscale) and 18052 (MariaDB, 127.0.0.1). The bench joins the engine network as `frappe`, so Frappe calls `http://api:8000` and the engine calls back `http://frappe:18050`. Sites: `talent.localhost` (demo, Arabic, Asia/Riyadh, Saudi Arabia) and `test.localhost` (automated tests).
- **App `ido_talent_ai`**: 11 DocTypes with the client's names, custom fields on Job Opening and Job Applicant (AI fields at permission level 1 = HR only), public Arabic form `/ai-apply/new` linked from the HRMS job page, the automatic path (after_insert → background job → AI Recruitment Job → engine → HMAC callback → AI Candidate Assessment), the applicant AI section (10 stages, evidence, strengths/gaps/raise, contradiction, duplicate, stale, override, decisions with reason), CV analysis dialog, list columns and filters, ranking page (groups, CSV, comparison), batch monitor, cycle map, settings synced with the engine, audit log, Arabic translations, sidebar and desktop icon for the v16 desk.
- **Engine additions**: impact preview (`POST /v1/jobs/{ref}/impact`), job deletion (`DELETE /v1/jobs/{ref}`), application time `applied_at` (orders duplicates and starts retention), duration in CV quotes levelled in code, later copies re-marked as duplicates when the original is scored afterwards.
- **Demo**: opening «مشرف أمن — الرياض» (HR-OPN-2026-0001) from the designation template, approved v1 (weights 30/20/15/15/8/7/5, rules nationality/height/weight/age), 25 synthetic applicants: 2017 filled in the real form in headless Chrome, 24 through the same endpoint with PDF, Word, scanned-image and corrupt CVs. Result: 17 ranked, 4 not eligible (height 2010, weight 2020, nationality 2011, age 2023), 2 needs review (2012 answer-vs-CV contradiction, 2021 mandatory answer blank), 2 duplicates (2016 → 2015, 2024 → 2003), damaged CV of 2013 assessed from the answers.
- Tests: engine 108 passed; Frappe app 11 passed on `test.localhost`; every desk screen rendered in headless Chrome as HR Manager with no JS errors.

Problems found while building and how they were fixed:
- The server disk is a busy HDD (~350 ms per fsync, ~1.7 s per CREATE TABLE even without fsync): an ERPNext + HRMS install was taking hours. The dev MariaDB now runs in memory (tmpfs); `start.sh` restores the latest bench backup when the database is empty and takes a backup every 2 hours. A full site with all apps installs in ~2 minutes.
- `frappe.enqueue(job_name=...)` is reserved by Frappe; the job argument is now `ai_job`.
- MariaDB 11.8 snapshot isolation: concurrent workers got error 1020 on the naming series. One collision rolled back a whole application request (the application was lost). Now the application request writes only its own row, the AI job is created by a background job, transactions are short around engine calls, conflicts are retried, and a 2-minute safety net queues missed applications.
- A retried job created a second engine candidate, which made applicants look like duplicates of themselves. The engine reference is now deterministic per application and the engine orders duplicates by the host's application time.
- Nationality labels came from framework translations, which changed after an asset build ("Saudi Arabia" lost its Arabic label) and made everyone «غير مستوفٍ». The app now has its own Arabic country table used for both the rule and the fact.
- The model gave «لمدة سنتين» level 100 for supervision; durations in CV quotes are now levelled in code (decision 6), so the 2012 contradiction is detected every time.
- A corrupt PDF makes Frappe's File doctype raise (it parses every PDF): the application is now saved without the file, with a note, and assessed from the answers.
- Deleting an applicant was blocked by its audit rows (dynamic link): the rows are now de-identified on deletion.
- Scheduled jobs created before the switch to Asia/Riyadh had a creation time in the future and would not run for hours; the setup now resets them.
- Bootstrap's `.collapse` hid the ranking groups; the class is now `tai-group`. A DocType marked `read_only` is hidden from lists in Frappe ("user cannot search"); the audit log is append-only by permissions instead.

Decisions taken alone (and why):
- **Public form as a www page** (`/ai-apply/new`), not a Web Form record: questions come from the approved profile per opening, the CV is uploaded with the application in one request, consent is mandatory, and the page is Arabic RTL with an English toggle. HRMS links to it through the opening's `job_application_route`, which the app sets when the profile is approved (no HRMS change).
- **Eligibility sentences on the HRMS job page** through `web_include_js` (no template override).
- **Opaque engine references** (`JA-` + keyed hash): Job Applicant names are e-mails in HRMS and must not reach the engine.
- **HR roles**: the AI section and the identity fields use permission level 1, given to HR Manager, HR User and System Manager (creates Custom DocPerm rows, removed on uninstall).
- **Number questions and languages are optional** in the demo profile, so "blank = not answered" is possible; select questions stay required. Height and weight are required in the form only when the opening has a rule on them.
- **HRMS's own Reject/Shortlist buttons** are hidden on the applicant form when the AI section is shown; the reasoned decision buttons replace them. Status changes made elsewhere are audited (see OPEN_QUESTIONS #19).
- **Not built from the demo form**: personal photo and certificates (not in the requirement list; a photo must never reach the AI; OPEN_QUESTIONS #18).
- Engine image builds use the default Docker builder: a build was started once by mistake on the shared `sdf-builder` (selected by default in the shell) and stopped after ~4 minutes; its cache was left untouched (not ours).

## Phase 7 — acceptance criteria, clean install, deployment guide

Done (branch `phase-7-acceptance`):
- `tools/ui/` (committed): the headless-Chrome tools used for the evidence — `frappe_ui.py` (CDP driver), `apply_via_form.py` (fills the public form like an applicant), `desk_shots.py` (renders every desk screen), `acceptance.py` (the checks below).
- **13 of 13 acceptance checks passed** in a real browser as Guest, HR Manager, HR User and Employee: A1–A6 and A8 of the client's criteria (A7 is about postponed features), plus the guide's continuation steps (weights/impact/v2, re-score all, CSV, comparison, settings in the engine, audit log). Report: `docs/ACCEPTANCE_REPORT.md`; screenshots and JSON: `docs/screenshots/acceptance/`.
- **Clean install** rehearsed on a separate bench: `bench get-app` from the app's git repository → new site with ERPNext + HRMS → `install-app` → `migrate` → app tests (11 passed) → `uninstall-app` (custom fields, permission rows and DocTypes removed) → Job Applicant still works. Script: `dev-frappe/clean_install.sh`.
- `docs/DEPLOY.md`: engine and app installation, settings, first opening, uninstall, and the open deployment questions.

Problems found and fixed:
- `bench init --clone-from` installs the cloned apps into the parent folder (path bug in bench 5.31); the rehearsal bench is built with local git clones and a fresh virtualenv instead.
- Git in the bench container refuses the host-owned app repository ("dubious ownership"); the rehearsal marks it as a safe directory inside the container only.
- On a website page, Frappe's `xcall` never settles when the server answers 403, so the role checks use `fetch` and read the status code.

Decisions taken alone:
- The acceptance run changes the demo (a decision, profile v2, an engine outage, test applications); the demo is rebuilt with `dev-frappe/reset_demo.sh` afterwards so Nadine starts from the clean state.
- The engine outage in A6 was produced by stopping our own `talentai-api` container for ~3 minutes and starting it again; nothing else on the server was touched.

## Phase 8 — talent pool (feature 13); comparison (feature 10)

Done (branch `phase-8-pool`):
- **Comparison** (feature 10) was built in phase 6 on the ranking page and checked in phase 7: 2–3 applicants of the same opening, criterion by criterion with their evidence.
- **Engine**: an embeddings gateway like the LLM one (`fake` | `local` | `cloud`), a new internal service `embed` (Qwen3-Embedding-0.6B on CPU, OpenAI-compatible, ~2.8 GB RAM, ~0.5–1 s per profile, no GPU), stage 10 «الفهرسة» indexes the verified profile after each screening (only with consent and inside the retention period), and `POST /v1/talent-pool/search`: hard rules first (code), then cosine similarity between the opening and the profile; excluded with the reason: consent withdrawn, retention ended, already applied, not eligible (with the failed rule), older duplicate. Withdrawn consent deletes the stored profile. 405 existing profiles re-indexed in ~6.5 minutes.
- **Frappe**: page «بنك المتقدمين» (`/desk/ai-talent-pool`) from an opening, the button «سحب موافقة المعالجة» on the applicant (reason required, audited; no new processing afterwards), second demo opening «مشرف أمن — جدة», and two demo cases (consent withdrawn: 2014; old application with ended retention: 2019). Result on the demo: 16 suggestions, 8 excluded with the reason.
- **Walkthrough** `docs/WALKTHROUGH.md` (Egyptian Arabic, guide order 0–15) with screenshots in `docs/screenshots/`, taken by `tools/ui/walkthrough_shots.py` on the clean demo; no JS errors.
- Tests: engine 109, Frappe app 13.

Decisions taken alone:
- **Embeddings on CPU in a separate service** rather than in the API/worker processes: the RQ workers fork per job (the model would load every time), the GPU cap of 0.40 is already used by vLLM, and an OpenAI-compatible endpoint keeps the provider switchable to cloud like the LLM. Model download ~1.2 GB and image 1.9 GB (both under the 5 GB rule), stored in our volume.
- **What is embedded**: the verified profile, not the raw CV: criteria with level and evidence, structured answers (no free text), and the first 1500 characters of the redacted CV. Identity never enters the vector.
- **One suggestion per person**: when the same ID token applied several times, the newest application is suggested and the older ones are listed as «طلب أحدث لنفس الشخص موجود».
- **Suggestions are filtered to the host's own applicants** in the app, because the engine tenant is shared with the console's test data on this server.
- **Old-application demo case**: the creation date of one synthetic application is set to 2024-09-15 in the dev site so its retention period has ended; marked as a simulation in `seed_demo.pool_cases`.
- The public HRMS pages follow the browser language for guests (standard Frappe); the walkthrough explains `?_lang=ar`. Our own form is Arabic first in any case.
- Form helper objects are exposed on `window` (Frappe evaluates form scripts inside a function), so they can be reached by tests.
