# 07 — Data profile (aggregates only)

Computed in the browser on 2026-10-12 with GET requests; up to 200 most recent records per DocType were sampled (all records fit). No names, e-mails, phones or file names are reproduced here.

## Record counts (`frappe.client.get_count`)

| DocType | Count | Notes |
|---|---|---|
| Staffing Plan | 2 | both submitted; departments "Security - D" and "Marketing"; company "Contracting EG" |
| Job Requisition ("Hiring Request") | **0** | the planning step is unused |
| Job Opening | 5 | all status Open; 2 published; created 2025-07-05 … 2026-03-01 |
| Job Applicant | 5 | created 2025-07 (1), 2025-11 (1), 2026-02 (2), 2026-03 (1); all created by logged-in users (none by Guest → none came through the public form) |
| Interview | 2 | both draft (docstatus 0) |
| Interview Feedback | 1 | |
| Job Offer | 3 | 2 submitted, 1 draft |
| Appointment Letter | 0 (sidebar shows no count) | |
| Employee Referral | 0 | |
| Job Opening Template | 0 | |
| Interview Type | 1 | "First Round - HR Interview", no designation, no expected skills |
| Job Applicant Source | 7 | |
| Skill | 1 | "Good Search" (test data) |
| Designation | 34 | 0 of 34 have a description; includes Arabic security roles (فرد امن, مدير قسم الامن) |
| Designation Skill rows | n/a (403 on get_count for the child table) | none visible on Designation forms sampled |
| Employment Type | 9 | Full-time, Part-time, Probation, Contract, Commission, Piecework, Intern, Apprentice, Cooptraining |
| Branch | 2 | Riyadh, Jeddah |
| Company | 13 | demo companies incl. "Al Nile Security Services Co." (SA) and "Contracting EG" (used by all recruitment data) |

The dataset is **test data**, far too small for any statistical conclusion; fill rates below describe how the demo was used, not production behaviour.

## Fill rate (% non-empty) per field

### Job Opening (5 records)

| Field | % | Field | % |
|---|---|---|---|
| job_title, designation, status, posted_on, company, department, employment_type | 100 | description | **60** (2 openings have none; lengths: 1 short <100 chars, 2 between 500–1999 chars) |
| location | 80 | closes_on | 60 |
| staffing_plan | 40 | planned_vacancies | 100 (value may be 0) |
| job_requisition | **0** | job_opening_template | 0 |
| vacancies, publish, prevent_duplicate_applicant, publish_applications_received, salary_per, publish_salary_range, currency, lower_range, upper_range | 100 | job_application_route | 0 |

Distributions: status Open 5 · publish 1 → 2, 0 → 3 · employment_type Full-time 4, Part-time 1 · location Riyadh 3, Jeddah 1, empty 1 · department Security - D / Marketing / Operations / Human Resources / Accounts 1 each · designation Customer Service Representative 2, Analyst 1, HR 1, Accountant 1 · prevent_duplicate_applicant 0 on all · publish_applications_received 1 on all · publish_salary_range 0 on all · salary_per Month on all.

### Job Applicant (5 records)

| Field | % | Field | % |
|---|---|---|---|
| applicant_name, email_id, status, country, applicant_rating (value 0 on all) | 100 | phone_number | 60 |
| job_title (opening) | 80 | designation | 80 |
| resume_link | **0** | resume_attachment | **0** |
| cover_letter | **0** | notes | 0 |
| source | 40 | source_name | 20 |
| employee_referral | 0 | currency / lower_range / upper_range | 80 / 100 / 100 (0 values count as filled) |

Distributions: status Accepted 2, Open 1, Shortlisted 1, Replied 1 · country Egypt 2, Saudi Arabia 2, Albania 1 · source empty 3, Recommendation 1, Linkedin 1 · applicant_rating 0 on all 5 · linked to a Job Opening **4**, not linked **1** · with resume attachment 0, with resume link 0, with cover letter 0 · distinct opening per applicant (each linked applicant points to a different opening).

Hiring pipeline view (kit): Open 1, Replied 1, Shortlisted 1, Accepted 2, Rejected 0, Hold 0.

### Job Requisition (0 records) — no fill data.

### Staffing Plan (2 records)

All header fields 100%. Detail rows: 1 per plan (designation Analyst: 3 vacancies, cost 15,000; designation Customer Service Representative: 2 vacancies, cost 1,000; current_openings 0 and 1).

### Interview (2 records)

| Field | % |
|---|---|
| job_applicant, job_opening, designation, status, scheduled_on, from_time, to_time, expected_average_rating, average_rating | 100 |
| interview_type | **0** |
| resume_link, interview_summary | 0 |

status Cleared 1, Pending 1 · designation Customer Service Representative 2 · docstatus 0 (draft) both.

### Job Offer (3 records)

| Field | % |
|---|---|
| job_applicant, applicant_name, applicant_email, offer_date, designation, company, status | 100 |
| job_offer_term_template | 33 |
| select_terms, terms, letter_head | 0 |

status Accepted 2, Awaiting Response 1 · docstatus 1 → 2, 0 → 1 · designation Customer Service Representative / HR / Accountant 1 each.

## Attachments (`File` with `attached_to_doctype` in Job Applicant, Job Opening, Job Requisition, Interview, Job Offer, Employee Referral)

| Metric | Value |
|---|---|
| Files | **1** (attached to a Job Applicant) |
| Extension | jpg (1) — a photo-type file, not a CV |
| Attached to field | none (sidebar attachment, not `resume_attachment`) |
| Private / public | private 1 / public 0 |
| Size | 74 KB |
| Uploaded by Guest | 0 |

No PDF/DOCX résumé exists on the site. There is nothing to test a parser against; a sample set must be collected from the client.

## Observations for the AI layer

1. Every "signal" field is empty on this demo: no résumé, no cover letter, no rating, no skills, no designation descriptions. The system has the slots but nobody has filled them.
2. Applicants were entered by HR users, not through the public form; the public path exists but is unused.
3. Planning (Job Requisition) is unused; openings are created directly and sometimes linked to a Staffing Plan (2 of 5).
4. Interview Type is not used on interviews (0%), so `expected_skill_set` → `skill_assessment` scoring in Interview Feedback cannot be exercised.
