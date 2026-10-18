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

## Round 2 — completion, design pass, full browser test, guide (autonomous, 2026-10-16)

### Part 1 — what was missing (merged as `p9-completion`)
- Frappe home page «التوظيف الذكي» (`/desk/ai-recruitment`): nine cards in the order Nadine gave, one line under each, live counts; HR Manager and HR User land on it after login (login hook), Arabic set for new HR users; a card the role cannot open shows «غير متاح لدورك».
- Nadine's decisions applied: dev-frappe scripts committed without `.env`; the status-change reason stays audit-only; only the default Docker builder (`make` refuses any other, `scripts/compose.sh`); the in-memory Frappe database is documented as test-only; a permanent test that an application is always saved (`test_application_is_always_saved`: queue down at commit, hook crash, audit down, DB conflict retried, AI off, damaged CV).

### Part 2a — design pass (branch `p10-design`)
Measured in a real browser on every screen at 1366, 1440 and 1920 px (public pages also at 375 and 390 px): `tools/ui/design_audit.py` reports overlapping text boxes, cut or off-screen text, page overflow, text under 11.5 px and contrast under WCAG AA. Before/after numbers and image pairs are in `docs/TEST_REPORT.md` §8.
- **Fonts**: IBM Plex Sans Arabic and IBM Plex Mono are served by the app and the console (OFL licence file included); no page calls Google Fonts any more.
- **Contrast and sizes**: the muted grey #6f7d9c (4.13:1) became #56627c; chip texts are darker; nothing is under 12 px.
- **Colours with one meaning**: green = eligible / high, amber = medium / needs review (contradiction, unreadable CV, AI draft), red = not eligible / low / failed, grey = stale / duplicate, blue = information / processing, purple = an HR edit; «إلزامي» is a neutral outlined chip.
- **Mixed text**: Latin words and numbers inside Arabic sentences are isolated (`T.mix`, `mix`); quotes are «…»; dates are readable Arabic dates; the engine writes its stage notes in Arabic with correct number agreement (`app/domain/arabic_text.py`) and now also in English (`note_en`) for the English toggle; method names and redaction keys have Arabic labels.
- **Layouts**: ranking rows put the strengths on their own line and wrap long references; the 10 stages follow the width of their own card; the console criteria editor fits at 1366 (no letter-by-letter «إلزامي», Arabic hints in the Arabic font, rules and questions stacked); the audit-log payload wraps in its cell.
- **Frappe look**: our cards inside the desk use Frappe's own card background, border and radius; HRMS labels shown on our screens are translated (87 strings in `translations/ar.csv`, «No.» → «م»), the applicant list hides the ID column that only showed «com», the answers grid hides the technical key.
- **Public job pages (HRMS)**: a scoped web stylesheet (`talent_ai_web.css`, `/jobs` and `/ai-apply` only) gives the grey texts AA contrast and 12.5 px labels; the HRMS templates are not modified.

Decisions taken alone:
- **No change to HRMS templates**: the public job pages are improved only with a stylesheet scoped by `body[data-path]` and with translations in our app.
- **Fonts bundled in the app** rather than loaded from Google: same look, no third-party request with the applicant's or HR's IP, works on a platform without internet access.
- **English stage notes are stored next to the Arabic ones** (`note_en`); screenings made before this change keep their Arabic note in English mode.

### Part 2b — full browser test (branch `p11-full-test`)
`tools/ui/full_test.py` (Playwright for Python with the server's Chrome; the Playwright MCP server was not available in this session) drives the whole system as nine kinds of user, through every CV type, the special cases and the console, and writes `docs/test-run/full_test.json`; `tools/ui/test_report.py` turns it into `docs/TEST_REPORT.md`. Screenshots (8-bit PNG) go to `docs/guide/images/roles/` and `docs/guide/images/test/` and are reused by the guide.
- **Roles**: the site has 52 roles; the recruitment-related ones were tested with their own users (Administrator, System Manager, HR Manager, HR User, Interviewer, Employee, Employee Self Service, a website applicant account, Guest) on 16 screens and 14 server calls each. HRMS v16 has no «Hiring Manager» or department-manager role.
- Problems found and fixed (each with a permanent test that fails without the fix): an RTF CV failed the screening (F1); «إعادة تقييم الكل» stopped at the first applicant who had withdrawn consent (F2); `profile.templates_for` had no HR check (S1); the «Employee» test users held no role because ERPNext strips it without an Employee record (S2); console fonts were sent as octet-stream (S3).
- Test-script mistakes corrected during the run (not product bugs): applicant 2009 was the wrong example of a blank answer (his CV supplies the evidence), the duplicate's e-mail, the dialog handling of the override case, and re-run e-mails.

Decisions taken alone:
- **Synthetic Employee records for the demo users** that need the Employee or Employee Self Service role (ERPNext removes those roles from a user without one).
- **A CV problem never fails a screening**, including a file the platform cannot read or the engine refuses: a note for HR and the assessment from the answers (decision 14 applied to the upload step too); only an engine outage is retried.
- **«إعادة تقييم الكل» skips applicants without consent** and reports how many; how to show them afterwards is OPEN_QUESTIONS #21.

### Part 3 — the guide (branch `p12-guide`)
`tools/guide/build.py` builds `docs/guide/talent-ai-full-guide.pdf` (Chrome `page.pdf`, A4, right to left, IBM Plex Sans Arabic) and `docs/guide/talent-ai-full-guide.docx` (python-docx) from the same content (`tools/guide/ch_*.py`), the real numbers of the clean demo (`facts.py` → `docs/guide/facts.json`) and 83 screenshot pages (`shots.py`, read-only on the demo; `docshots.py` for the terminal views). Sixteen chapters in Egyptian Arabic for HR readers; a box «للفريق التقني» on each page names the inventory items the page explains, and the appendix lists the rest.
- **Writing rules checked by code** (`lint_ar.py`): no «يتم», «حيث», «وذلك»; every line starts with an Arabic word; English only at the end of a line or on its own line; no two sentences in a row start with the same word.
- **Page checks by code** on the PDF and on the Word file converted to PDF by LibreOffice: no picture outside the page, no two text lines drawn over each other, nothing in the footer but the page number, no text at the paper edge, every chapter page starts with its own title (so a page that only holds the tail of the previous one is caught). Every page of both files was also looked at as an image.
- **Inventory from the code** (`inventory.py` → `docs/guide/inventory.json`) and `docs/guide/COVERAGE.md` (guide page, screenshot and test of every item); `coverage_check.py` reads the routes, DocTypes, endpoints and commands from the code again and compares.
- Bug found while taking the screenshots: the Talent AI section of the Job Opening sat in the «تفاصيل الراتب» (Pay Details) tab (G1, fixed with a test).
- Found by the final test run: the real `make install` of the commands check is a plain `uv sync`, which keeps only the `dev` group, so it removed PaddleOCR, Presidio and spaCy from the local `.venv` and the two English-name redaction tests were skipped (110 passed, 3 skipped). Restored from the uv cache with `uv sync --group documents --offline` (112 passed, 1 skipped, as before); the engine README now names that command.

Decisions taken alone:
- **Screenshots cut to the part the page explains**: a screen taller than the room left on its page keeps its top part, cut on an empty pixel row, so it prints at the full text width and stays readable; the full screenshots stay in `docs/guide/images/steps/`.
- **Page numbers read from the printed PDF**: the contents and the index take their numbers from the PDF's named destinations after a first print, and the PDF is printed again; the Word file uses PAGEREF fields.
- **The Word file is checked through LibreOffice**: there is no Microsoft Word on the server, so the Word file is converted to PDF by LibreOffice for the page checks; Word may break a few pages differently, and the page fields keep the numbers right.

## Round 3 — consent defaults (OPEN_QUESTIONS #20, #21), 2026-10-16

Nadine's defaults, in force until the client confirms (written as such in `OPEN_QUESTIONS.md`):
- **#20 Paper application without consent**: saved as usual, never sent to the AI. AI status «بانتظار الموافقة» (Awaiting Consent), its own ranking group and a note on the ranking page. HR records the consent with its source, which is mandatory (button «تسجيل الموافقة», `api.record_consent`); `ai_consent_source`, `ai_consent_recorded_by`, `ai_consent_on` and an audit row keep who and when; the screening starts by itself.
- **#21 Consent withdrawn**: out of the ranking at once, into the closed group «مستبعد: سحب الموافقة» with no score and no details. The engine (`PUT /v1/candidates/{ref}` with `consent: false`) erases the CV documents and their files, the structured profiles, the talent-pool index, every screening and criterion result, the facts and answers it held, and the findings in its audit trail; only the reference stays, with the jobs it had applied to (`consent_withdrawn_at`, `withdrawn_from`, Alembic `b9f7e8a1c2d3`) so its ranking and the talent pool can list it. Frappe drops its copy (assessment, evidence, AI fields, findings in the audit details) and keeps the application. A screening running at that moment writes nothing (the worker locks the candidate row before it writes); a late callback is refused; queued jobs become «أُلغيت» (Cancelled); with the engine down the erasure is retried every two minutes (`erase_pending`).
- `make install` runs `uv sync --group documents`.
- Tests: engine `tests/test_consent.py` (8; engine 120 + 1 skipped), Frappe 4 more (22); browser checks K16 (result 11.1 s after the consent) and K17 (out of the ranking in 4.0 s, CV file gone from the engine) in `tools/ui/full_test.py`, 40/40; design audit 99 screens, 0 issues, 0 JavaScript errors.
- Guide: seven pages in chapter 9 (cases 9 أ–هـ and 10 أ–ب) with screenshots from the clean demo (two paper applications in `demo_data.json`, `seed_demo.paper_cases`), and the privacy, FAQ, open-question, glossary and fixed-bug pages updated; PDF and Word 130 pages each; inventory 576 items, MISSING 0.
- Bugs found on the way (TEST_REPORT §1): E1 a deleted candidate's CV file stayed on the volume; E2 a CV file shared by two candidates was deleted with the first one; E3 `make install` dropped the documents group; E4 the app tests and the test site's scheduler filled the shared `long` queue with jobs for an engine nobody serves; E5 the 2-minute safety net and the batch page compared site times with the database's UTC clock (three hours off).

Decisions taken alone:
- **Frappe's copy of the AI result goes too**: «من غير درجة ولا تفاصيل» has to hold on every screen (applicant form, list, audit details), not only in the ranking; the application, its answers, its CV file and the HR decision fields stay.
- **A withdrawal is final for that application**: «تسجيل الموافقة» is refused after a withdrawal; a person who consents again applies again.
- **The engine keeps the reference only**: a bare candidate row (no facts, answers, ID token, documents or results) so the engine's own ranking, the console and the talent pool can show «مستبعد: سحب الموافقة» for any host system, not only Frappe.
- **The earliest later copy becomes the original**: when the original of a duplicate pair withdraws, the person's next application is ranked in its place.
- **A paper consent carries the current consent text version**: the paper form is assumed to show the same text; the client confirms (#20).
- **Score 0 means no score in the list**: Frappe Float columns cannot be empty, so the list shows a score only for a finished screening.

## Round 4 — Nadine's review of the guide, 2026-10-16

System fixes first (branch `p14-review`), then the guide.
- **V1 Redaction leak (priority 1)**: the e-mail of an Arabic text PDF reached the local model. Cause: Word/LibreOffice write Arabic pages in visual order and PyMuPDF's per-span reversal moved the dot of the address to the end of the line (`demo.2001@example com.`), which the e-mail pattern missed. The PDF text is now rebuilt from the characters and their positions (`app/documents/pdftext.py`: rows by baseline, visual order, the inverse of the bidi reordering with the W4 rule for numbers, lam-alef ligatures kept, page-level direction). The redaction patterns tolerate spaces and moved dots, a fail-safe sweep runs at the end of every redaction, and the pipeline runs a last `leak_check` before any model call (flag `redaction_guard`, audit event). `scripts/reprocess_cvs.py` re-extracted and re-redacted every stored CV in place: 220 documents, 12 with a leak before (all Arabic text PDFs: 4 demo applicants and 8 console seed candidates), 0 after; their screenings became stale and were re-scored. The 12 leaks had gone to the local model on this server only (no outside service).
- **V2 Numbers scrambled** in Arabic PDFs (`من14. فرد`): same fix; the years read from a line are tested.
- **V3 Weak OCR lines as evidence**: a line under `OCR_MIN_CONFIDENCE` is replaced by a marker before the model and before any quote check (`app/pipeline/stages/cv_text.py`), stored in `versions.weak_lines`, shown struck through in the CV panel and the analysis («ضعيف — لا يُقبل كدليل»).
- **V4** red banner on the assessment card when the CV was not read; **V5** the design picture had two test applications with the same name (different IDs, not a missed duplicate): the picture shows three rows.
- Guide: the whole public form in two pictures, one distinctive picture per HR role, bigger home page and cycle map, the criteria grid with wider columns, the console CV picture of the worked example, the number `10487`, the PDPL answer, test codes moved to the technical boxes, one application versus a thousand explained.
- Tests: engine 129 + 1 skipped (`tests/test_pdftext.py` new); Frappe 22; browser 40/40 (V1–V5 added to the report); design audit 33 screens, 0 issues. Guide: PDF and Word 134 pages each, inventory 581 items, MISSING 0.

Decisions taken alone:
- **PDF text is rebuilt from characters, not spans**: the only way to get an address, a number or a full stop back where it belongs in an Arabic page; checked against python-bidi on every synthetic line.
- **A weak OCR line is removed, not down-weighted**: the model never sees it, so it cannot quote it; HR sees it in the analysis for a manual check.
- **The leak guard is a second gate**: the redaction already sweeps; the guard before the model call exists so a future extraction bug can never reach a model silently (it flags and audits).


## Round 5 — Nadine's review of the guide v2, 2026-10-16

Guide only (branch `p15-guide-v3`); no engine or Frappe code changed.
- **Form pictures**: the public form in three pictures cut at its section headings (details, screening questions, CV + consent + submit), each caption listing exactly what the picture shows (`shots.py` `snap_parts(cuts=…)`). The browser already runs with locale `ar-SA` and the Riyadh time zone; the date field still shows the browser's own `mm/dd/yyyy` because headless Chrome draws the Arabic placeholder with broken, unshaped letters whatever is tried (`--lang`, `LANG`/`LANGUAGE`, old headless, other fonts) — the caption says the field follows the applicant's browser language.
- **Speed numbers** (manager page, two FAQ answers) now come from the raw bench reports (`facts.py` reads `talent-engine/eval/reports/*-bench-*.json`): 100 applicants = 46 without a CV + 54 with a text PDF (Word → LibreOffice), 0 scanned; per-applicant pipeline mean 13.9 / 18.1 / 28.0 s with 2 / 4 / 8 workers; 100 × 28.0 ÷ 8 = 350 s against 325 s measured; one application 10 s (no CV) to 53.3 s (scanned); 54 min written as «حوالي ساعة». Same facts added to `docs/EVALUATION_REPORT.md`.
- **Bug table row D**: the 10,487 explained from `TEST_REPORT.md` §8 (110 screens × widths, every text box counted: 6524 contrast + 2870 small font + 825 overlap + 268 off screen) and the two remaining notes named (the HRMS «قدّم الآن» fixed button on the phone job page); `facts.py` parses the section (`F["design"]`).
- **Home page**: `snap_parts` grows the window to the whole content first (the desk scrolls inside a container, so the ninth card was cut at the first screen) and pads the clip; cards 5–9 are now whole in the second picture.
- Small: «العميل (PDPL)» in the open-questions table; the settings caption gives the full callback URL (the field is narrower than the text; the status card shows it whole); `SHOTS_ONLY=public,home,…` reruns one group of screenshots. All screenshots retaken on the rebuilt demo so the pictures and the facts come from the same state.

## Round 6 — Nadine's review of the gold set, 2026-10-18

Evaluation and docs only (branch `p16-gold`); no engine or Frappe behaviour changed.
- **How the expected levels are made**: by `eval/make_gold.py`, not by hand — a numeric answer through the engine's own `level_from_rubric`, a select answer by its fixed position, the languages answer by the demo rule, each free-text answer written for one rubric level (five texts). Every «expert level» wording replaced by «المستوى المتوقع حسب جدول المعايير» with the note that it is not a human judgement (guide, EVALUATION_REPORT, ARCHITECTURE, TESTING, PLAN, GOLD_SET.md).
- **Gold set**: supervision years never exceed security years (6 applicants corrected: 002, 011, 012, 020, 026, 035); the gold job's age rule is 21 as on the demo form; five eligibility edge cases appended (036 non-Saudi → not eligible, 037 age 20 → not eligible, 038 age 21 → eligible, 039 height blank → needs review, 040 age blank → needs review). 55 applicants.
- **Evaluation rerun** (`8b-v1-r6`, rerun + name-swap): level exact 98.5%, within one step 100%, evidence 100%, eligibility 100% (all five edge cases as expected), flags 100%; split: code-levelled 100% of 305 judgements, model-judged 69% exact / 100% within one step of 16 judgements, measured on 5 distinct free texts and 31 CV documents; rerun identical 98% (54 of 55), name-swap 100%. **1 of 55 failed in both passes (GOLD-SEC-015; GOLD-SEC-023 in the second pass only)**: `LLMOutputError` — the profile extraction JSON was cut off by the output limit and could not be repaired after 3 attempts → «Failed» as decision 14 prescribes. Left as is this round; to fix next with a larger output budget and a shorter-prompt retry for the profile call.
- OPEN_QUESTIONS #22 (supervision years > security years: flag and send to review?) and #23 (languages rubric: English only = 0, Arabic only = 50 — intended?).
- `eval/run.py` reports the code/model split, the number of distinct free texts and CV documents; `facts.py` reads the round-6 run, the split and the gold-set size from the report.
