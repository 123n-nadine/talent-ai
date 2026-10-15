# 00 — Summary: Recruitment module discovery on demo.hs1.ido.sa

Read-only discovery, 2026-10-12, GET only, nothing saved/submitted/uploaded. Personal data was aggregated in the browser and blurred in screenshots. Full detail in files 01–09, per-DocType metadata in `03_doctypes/`, field matrix in `04_fields_matrix.csv`, request log in `_log.md`.

## Platform

| Item | Value |
|---|---|
| Frappe / ERPNext / HRMS | 16.31.0 / 16.32.0 / **17.0.0-dev (develop branch)** |
| Custom apps touching HR | `hr_ksa_customization` (module HR KSA: KSA payroll, termination, onboarding docs — no recruitment DocTypes), `ido_design` (theme + "IDO Desk kit": recruitment panels, Hiring pipeline page, 3 custom fields + 5 property setters on Job Requisition / Job Opening created 2026-10-04) |
| Language / TZ | site default Arabic, user English; TZ Africa/Cairo; public form renders Arabic RTL with `?_lang=ar` |
| Scheduler | **disabled** (last job 2025-08-21) → expired openings stay Open, reminders never sent |
| Integration surface | REST reachable with session; no Webhooks, no Server/Client Scripts, no Notifications, no Assignment Rules, no Workflows on recruitment DocTypes; no AI/OCR/LLM feature anywhere |

## The recruitment flow as it really works (see 05_relationships.md)

Staffing Plan ("Workforce plan", 2 submitted) → *(Job Requisition = "Hiring Request", 0 records, unused)* → **Job Opening** (5, all Open, 2 published, linked to a plan in 2 cases) → publish → public `/jobs` portal → job page → **"Apply Now"** → standard Web Form `job-application` (`/job_application/new?job_title=<ID>`, anonymous, 12 data fields, one résumé Attach) → **Job Applicant** (5; all entered by HR, none via the form; 1 without an opening) → status pipeline Open → Replied → Shortlisted → Accepted (Rejected / Hold) shown in the custom **Hiring pipeline** page → Interview (2 drafts) → Interview Feedback (1) → Job Offer (3) → "Create Employee". All DocTypes are standard HRMS; there is **no custom recruitment DocType**.

## Key findings

1. **No eligibility data exists on the applicant.** Job Applicant has only name, e-mail, phone, country of residence, source, cover letter, résumé link/attachment, salary expectation. Nationality, national ID, date of birth, gender, height, weight, photo, certificates are all **missing** (some exist on Employee only, post-hire).
2. **No place to define rules per job.** Job Opening has title, designation, department, employment type, location, description, salary range; no required-nationality/age/height/weight, no skills table. Skills exist only as `Designation.skills` (custom field, empty) and in Interview Type / Interview Feedback.
3. **Every signal field is empty on the demo**: 0 résumés, 0 cover letters, rating 0 on all applicants, 0 of 34 designations with a description, 2 of 5 openings without description (the kit itself flags this as a hard "readiness" failure).
4. **The IDO Desk kit already adds read-only intelligence** (Readiness checklist, Candidates board, Workforce-plan seat accounting, "Where this applicant stands", Hiring pipeline, workspace figures) through whitelisted methods `ido_design.ido_desk.hr_gaps.api.panels / evaluate / list_extras` and `hr.hiring_pipeline`. An AI panel could follow the same pattern, but the app is shared across clients.
5. **Public form is standard and anonymous**: single Attach (any file type), no photo, no multiple attachments, no duplicate protection (`prevent_duplicate_applicant` = 0), Arabic available only via `_lang=ar`.
6. **Job Applicant records are keyed by e-mail** (legacy) while the DocType now uses a series; the talent-pool dedupe key is undefined.
7. **The HR team's "many filters" are ad hoc**: no saved filters, no list settings on this demo.

## Biggest gaps for an AI CV-screening layer (08_gap_analysis.md)

| Gap | Impact |
|---|---|
| Applicant facts (nationality, ID, DOB, gender, height, weight, photo, certificates) not captured | hard filters cannot run; needs custom fields + a client copy of the web form |
| Rules per opening not modelled | nowhere to read thresholds; needs fields or a rule table on Job Opening / Template |
| No AI output slots (score, rank, eligibility, summary, parsed CV, audit) | only `applicant_rating` (0–5) and `notes` (140 chars) exist |
| No trigger (webhook/hook) and scheduler off | scoring cannot be event-driven on this site as-is |
| No sample CVs | parser cannot be tested; need anonymised seed data |

## Top 10 open questions (full lists in 09_open_questions.md)

1. Exact hard rules per role (nationality, height, weight, age) and whether they are per Designation or per opening.
2. Are physical/ID values self-declared or verified, and may an unverified value reject?
3. Which documents are mandatory at application (photo, ID, licences, certificates)?
4. Who writes the job description / competencies, in which language, and where (Opening, Template, Designation)?
5. What output does HR want (eligibility flag, score, rank, summary) and may the AI change `status`?
6. How should the talent pool work: auto-rematch to other openings or tag only? Dedupe key?
7. Which app should hold client-specific fields (`hr_ksa_customization`, new app, or `ido_design` kit)?
8. Production platform: HRMS version freeze, scheduler enabled, time zone Asia/Riyadh, API user with key?
9. Can the standard web form be cloned with extra Attach fields for Guest, and what are upload limits?
10. Can anonymised applicants with real-looking PDF/DOCX CVs be seeded on the demo?

## Deliverables

`01_environment.md` · `02_navigation_map.md` · `03_doctypes/*.md` (30 DocTypes + README) · `04_fields_matrix.csv` (246 fields) · `05_relationships.md` · `06_web_form.md` · `07_data_profile.md` · `08_gap_analysis.md` · `09_open_questions.md` · `screenshots/` (01, 02, 10–12, 20–21, 30–31, 40, 50–53, 60–61) · `_log.md` (141 API calls: 128×200, 8×404, 3×417, 2×403) · `_raw_*.json` (scrubbed working files).
