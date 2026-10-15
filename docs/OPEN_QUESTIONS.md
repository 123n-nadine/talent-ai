# Open questions (ours, living list)

Questions we still need answered to finish or deploy. The discovery's own lists are in `reference/discovery/09_open_questions.md` (read-only); this file tracks what matters for the build. Add the date when a question is answered and keep the answer here.

| # | Question | Who answers | Needed by | Status |
|---|---|---|---|---|
| 1 | Production HRMS commit on the `develop` branch (the demo runs 17.0.0-dev). Our dev bench pins the develop HEAD of the day it is built and records it in `dev-frappe/VERSIONS.md`; production must be pinned the same way | Frappe team | Phase 6 | open |
| 2 | Background **workers** on the production site: `frappe.enqueue` (queue `long`) needs RQ workers, not the scheduler. The **scheduler** is only needed for the hourly retry of Failed jobs. The demo has the scheduler disabled (last job 2025-08-21); the gap analysis in `reference/discovery/08_gap_analysis.md` wrongly says `enqueue` depends on the scheduler | Frappe team | Phase 6 (dev) / deploy | open |
| 3 | How much GPU memory does the Luna stack (`remote-sdk`, `video-agent`, user awais) need when healthy? Our cap is 0.40 (~9.8 GB) and can be raised to 0.50 if Luna needs < 6 GB | Nadine asks awais | Phase 3 | open |
| 4 | Where is this GPU server physically (inside KSA or not)? Decides whether real CVs may ever be processed here under PDPL. Until answered: synthetic data only | Abdullah + client | before any real data | open |
| 5 | CV upload limit and allowed types for Guest on the web form (`allow_guests_to_upload_files` = 0 and `max_file_size` = 0 on the demo); does Frappe v16 allow a child table with Attach fields on a web form for Guest (needed for certificates)? | Frappe team | Phase 6 | open |
| 6 | Exact hard-rule values per role (nationality, height, weight, age range) and whether they are per Designation or per opening. `age >= 18` is a placeholder | Abdullah + client | Phase 1 seed is a placeholder; real values before acceptance | open |
| 7 | Consent text (Arabic) for the application form, and the retention period for applicants' data | Client (PDPL) | Phase 6 | open |
| 8 | Dedicated API user / key on the client site for the engine callback, with minimum permissions | Frappe team | deploy | open |
| 9 | Production time zone (demo runs Africa/Cairo; our dev site uses Asia/Riyadh) | Frappe team | deploy | open |
| 12 | (answered 2026-10-15, see EVALUATION_REPORT) Judge quality of Qwen3-8B-AWQ on Turing: generation ~45 tokens/s, one applicant with a CV takes ~15–20 s (profile + judgement). The gold set (phase 4) decides whether the 8B model is good enough or a 14B/Arabic model is needed; vLLM on this GPU runs with the Triton attention backend (no FlashAttention) | us | phase 4 | open |
| 13 | The phase-4 accuracy (98% exact levels) is measured on **synthetic** applicants. Real accuracy needs the client's HR to label 30–40 real applications (after redaction, inside the client's environment) with the expected level per criterion; then rerun `eval/run.py` on that set | Abdullah + client HR | before acceptance | open (Nadine, 2026-10-15) |
| 11 | OCR confidence threshold: PaddleOCR on the synthetic scanned Arabic CV scores ~0.74 (length-weighted). The 0.80 default sends every scan to Needs Review. Calibrate on the gold set (phase 4) against real-looking scans before deciding | us | phase 4 | open |
| 10 | RQ worker overhead: the pipeline takes ~0.5 s per application with the fake provider, but each RQ job adds ~1.5 s (fork + new DB engine per job). Options: keep a warm engine/session factory in the worker process, batch several screenings per job, or more workers. Decide with the real numbers of the phase 4 report (time per 1000) | us | phase 4 | measured in phase 4: minor next to LLM time (EVALUATION_REPORT §2) |

## Answered

| # | Question | Answer | Date |
|---|---|---|---|
| A1 | What happens with a corrupt or unreadable CV? | Screening continues from the form answers with flag `cv_unreadable`; `Failed` only for engine errors after 3 attempts | 2026-10-15 |
| A2 | Does a client-specific web form (`job-application-ksa`) exist? | Not on the demo; only the standard `job-application`. We add our own form | 2026-10-15 |
| A3 | Separate console port? | No. The console is served under `/console` on port 18000 | 2026-10-15 |
| A4 | Who owns the AI/OCR provider settings? | The engine. Frappe reads/writes them through `/v1/settings`; `.env` holds defaults only | 2026-10-15 |
| A5 | Is the national ID sent to the engine? | Never raw. Only `id_token = HMAC-SHA256(national_id, id_token_secret)` for duplicate detection | 2026-10-15 |
| A6 | Time zones | Engine stores UTC; dev Frappe site Asia/Riyadh | 2026-10-15 |
| A7 | GPU cap and ports | Option A (0.40) and the port table in `SERVER_REPORT.md` §5 approved | 2026-10-15 |
