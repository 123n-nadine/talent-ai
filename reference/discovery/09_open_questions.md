# 09 — Open questions

## For Abdullah (business / client side)

1. **Hard rules per job**: which roles have nationality / height / weight / age rules, and what are the exact thresholds? Are they fixed per Designation (e.g. "فرد امن") or decided per opening?
2. **Verification**: are height, weight, DOB and national ID self-declared in the application, or verified later (medical check, Absher/Yakeen)? Should an unverified value already reject a candidate, or only flag it?
3. **National ID**: is it the Saudi national ID only, or also Iqama for non-Saudi roles? Must the ID be unique across the talent pool (dedupe key)?
4. **Photo and certificates**: which documents are mandatory at application time (photo, ID copy, security licence, high-school certificate, driving licence…)? Any limits on size/type?
5. **Job description source**: will HR write the description on the Job Opening, on the Job Opening Template, or on the Designation? Who owns the Arabic version? (Today 2 of 5 openings and 0 of 34 designations have a description.)
6. **Competencies**: does the client have a skills/qualification catalogue, or should the AI derive criteria from the free-text description? Should skills live on Designation (reusable) or on the opening?
7. **Ranking output**: what should HR see — a pass/fail eligibility flag, a 0–100 score, a rank within the opening, a short summary, or all of them? Where in the pipeline is the score used (before "Shortlisted"?).
8. **Talent pool**: when an applicant does not match the applied opening, should the AI automatically propose other open openings (and change `job_title`), or only tag the candidate?
9. **Decision authority**: may the AI change `Job Applicant.status` (e.g. to Rejected) automatically, or only recommend? Any legal/PDPL constraints on automated rejection and on storing CVs?
10. **Volume and language**: how many applications per opening are expected, and in which languages are CVs (Arabic scans, English PDFs, photos of paper CVs)? This decides OCR needs.
11. **Channel**: will applicants use the Frappe public form (`/jobs`), a mobile app (ido_api), or walk-in data entry by HR? Today all 5 applicants were entered by HR, none through the form.
12. **Current filters**: which list filters does the HR team actually use today (fields and values)? None are saved on the demo.

## For the Frappe team (customization / permissions / platform)

1. **Which app owns recruitment customizations?** `ido_design` (module "IDO Desk", shared theme/kit for all I Do clients) created the Job Requisition custom fields and Job Opening property setters on 2026-10-04. Should client-specific AI fields go into `hr_ksa_customization`, a new app, or Customize Form fixtures?
2. **Production environment**: is the scheduler enabled there (`enable_scheduler` = 0 on the demo, last scheduled job 2025-08-21)? Background jobs are needed for async scoring and for `close_expired_job_openings`.
3. **HRMS version**: the demo runs `hrms 17.0.0-dev` (develop) on Frappe 16.31. What will production run, and when is it frozen? Field names used in this report may change on develop.
4. **Job Applicant naming**: old records are named by e-mail, new ones by `HR-APP-.YYYY.-.#####`. Will the data be migrated? E-mail-named records expose PII in URLs and screenshots.
5. **Web form**: can we clone the standard `job-application` Web Form (is_standard = 1) into a client form with extra fields and multiple Attach fields, and point `Job Opening.job_application_route` to it? Does v16 support child tables with Attach fields on web forms for Guest?
6. **Guest uploads**: confirm the allowed file types/size for Guest uploads via web form (`allow_guests_to_upload_files` = 0, `max_file_size` = 0) and whether private files are default for web form attachments.
7. **Integration surface for the AI layer**: preferred mechanism — Webhook (0 exist today), `doc_events` hook in an app, or Server Script (4 exist, Server Scripts enabled)? Can we get an API user with an API key and a restricted role instead of System Manager?
8. **Permissions**: who may read `resume_attachment` files (private)? The AI service needs file read access; proposed `national_id` field should be permlevel-restricted.
9. **IDO Desk kit**: is `ido_design.ido_desk.hr_gaps.api.panels` the intended place to surface an AI screening panel on Job Applicant / Job Opening, or should we add a separate form section? Who maintains the kit (it is minified; source repo access needed).
10. **"Hiring Request" relabel**: where is the Job Requisition → "Hiring Request" label coming from (Translation record, kit)? Needed so documentation and training match the UI.
11. **Language**: should the public form default to Arabic (`_lang=ar`) for the client's careers link, and should a language toggle be added to `/jobs`?
12. **Time zone**: the site runs on Africa/Cairo; the client is in KSA. Interview times and "closes on" logic will be off by one hour unless production uses Asia/Riyadh.
13. **Test data**: can the Frappe team seed realistic anonymised applicants with PDF/DOCX CVs on the demo (currently 0 résumé files), so the AI layer can be tested without real PII?
