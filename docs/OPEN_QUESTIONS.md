# Open questions (ours, living list)

Questions we still need answered to finish or deploy. The discovery's own lists are in `reference/discovery/09_open_questions.md` (read-only); this file tracks what matters for the build. Add the date when a question is answered and keep the answer here.

| # | Question | Who answers | Needed by | Status |
|---|---|---|---|---|
| 1 | Production HRMS commit on the `develop` branch (the demo runs 17.0.0-dev). Our dev bench pins the develop HEAD of the day it is built and records it in `dev-frappe/VERSIONS.md`; production must be pinned the same way | Frappe team | Phase 6 | open |
| 2 | Background **workers** on the production site: `frappe.enqueue` (queue `long`) needs RQ workers, not the scheduler. The **scheduler** is only needed for the hourly retry of Failed jobs. The demo has the scheduler disabled (last job 2025-08-21); the gap analysis in `reference/discovery/08_gap_analysis.md` wrongly says `enqueue` depends on the scheduler | Frappe team | Phase 6 (dev) / deploy | open |
| 3 | How much GPU memory does the Luna stack (`remote-sdk`, `video-agent`, user awais) need when healthy? Our cap is 0.40 (~9.8 GB) and can be raised to 0.50 if Luna needs < 6 GB | Nadine asks awais | Phase 3 | open |
| 4 | Where is this GPU server physically (inside KSA or not)? Decides whether real CVs may ever be processed here under PDPL. Until answered: synthetic data only | Abdullah + client | before any real data | open |
| 6 | Exact hard-rule values per role (nationality, height, weight, age range) and whether they are per Designation or per opening. `age >= 18` is a placeholder | Abdullah + client | Phase 1 seed is a placeholder; real values before acceptance | open |
| 7 | Consent text (Arabic) for the application form, and the retention period for applicants' data | Client (PDPL) | Phase 6 | open |
| 8 | Dedicated API user / key on the client site for the engine callback, with minimum permissions | Frappe team | deploy | open |
| 9 | Production time zone (demo runs Africa/Cairo; our dev site uses Asia/Riyadh) | Frappe team | deploy | open |
| 13 | The phase-4 accuracy (98% exact levels) is measured on **synthetic** applicants. Real accuracy needs the client's HR to label 30–40 real applications (after redaction, inside the client's environment) with the expected level per criterion; then rerun `eval/run.py` on that set | Abdullah + client HR | before acceptance | open (Nadine, 2026-10-15) |
| 15 | MariaDB 11.8 runs with `innodb_snapshot_isolation=ON`: concurrent writers get error 1020 instead of waiting. The app now keeps transactions short and retries conflicts; which MariaDB version and isolation settings does the client platform use? | Frappe team | deploy | open (2026-10-16) |
| 16 | Public form rate limit: 20 applications per IP per 10 minutes (site config `talent_ai_apply_limit`). Applicants applying from one office or kiosk share an IP; what limit does the client want? | Abdullah + client | deploy | open (2026-10-16) |
| 17 | Arabic for HRMS's own labels: HRMS develop ships `ar.po` with many empty strings. Round 2 fills the 87 recruitment strings our screens show (Job Opening, Job Applicant, Interview buttons, the public job pages) in the app's `translations/ar.csv`, and fixes «No.» → «م» and «Apply Now». The client's `ido_design` app may translate them differently; on the real platform, check which translation wins (the app installed last) | Frappe team | deploy | open (updated 2026-10-17) |
| 18 | The demo's form also has «الصورة الشخصية» and «الشهادات». Not built: the requirement list asks for an optional CV only, and a photo must never reach the AI. Add certificates as plain attachments (not read by the AI)? | Abdullah + client | phase 2 | open (2026-10-16) |
| 20 | Applications entered by HR in the desk (paper forms) have no consent record, so the AI does not process them (consent is required). Should HR be able to record a paper consent (with the form version and a reason) so these applications are screened too? | Abdullah + client | before go-live | open (2026-10-17) |
| 21 | After a new profile version, an applicant who withdrew consent keeps the old result, now «قديم», in the stale group of the ranking (no new processing is allowed, so it never leaves it). Show these applicants in their own group «سحب الموافقة» instead, or hide their old result? | Abdullah + client | before go-live | open (2026-10-17) |

## Answered

Rows `Qn` answer open question n above; rows `An` are other decisions.

| # | Question | Answer | Date |
|---|---|---|---|
| A1 | What happens with a corrupt or unreadable CV? | Screening continues from the form answers with flag `cv_unreadable`; `Failed` only for engine errors after 3 attempts | 2026-10-15 |
| A2 | Does a client-specific web form (`job-application-ksa`) exist? | Not on the demo; only the standard `job-application`. We add our own form | 2026-10-15 |
| A3 | Separate console port? | No. The console is served under `/console` on port 18000 | 2026-10-15 |
| A4 | Who owns the AI/OCR provider settings? | The engine. Frappe reads/writes them through `/v1/settings`; `.env` holds defaults only | 2026-10-15 |
| A5 | Is the national ID sent to the engine? | Never raw. Only `id_token = HMAC-SHA256(national_id, id_token_secret)` for duplicate detection | 2026-10-15 |
| A6 | Time zones | Engine stores UTC; dev Frappe site Asia/Riyadh | 2026-10-15 |
| A7 | GPU cap and ports | Option A (0.40) and the port table in `SERVER_REPORT.md` §5 approved | 2026-10-15 |
| Q5 | CV upload for Guests on the application form | We do not use a Web Form: our public page posts to `ido_talent_ai.api.apply`, which accepts PDF, DOCX, DOC, RTF, JPG and PNG up to 10 MB and stores the CV as a private file attached to the Job Applicant. Certificates: see #18 | 2026-10-16 |
| Q10 | RQ worker overhead | Measured in phase 4: minor next to LLM time (EVALUATION_REPORT §2); no change needed | 2026-10-15 |
| Q11 | OCR confidence threshold | Stays 0.80: the synthetic scans read at 0.91. Recalibrate with real scans together with #13 | 2026-10-15 |
| Q12 | Judge quality of Qwen3-8B-AWQ | Good enough: 98% exact levels, 100% within one step, 100% evidence on the gold set (EVALUATION_REPORT) | 2026-10-15 |
| Q14 | Commit the dev bench scripts? | Yes, without `.env` (Nadine). Done: `dev-frappe/` is in git with `.env.example` and `init_env.sh` | 2026-10-16 |
| Q19 | Enforce a reason for every status change? | No: status changes outside the Talent AI buttons stay audited only (Nadine). The Talent AI buttons always require a reason | 2026-10-16 |
| A8 | Which Docker builder may we use? | Only the daemon's default builder (Nadine). `make build`/`make up` force it (`override BUILDX_BUILDER := default` + `builder-check`); `talent-engine/scripts/compose.sh` for direct compose calls | 2026-10-16 |
| A9 | Frappe MariaDB in memory? | Only on the local test bench, for speed on this server's slow disk (backups every 2 hours, restored on start). Production uses the platform's normal disk-based MariaDB (DEPLOY.md) | 2026-10-16 |
