# 06 — Public application flow and Web Form

Screenshots: `50_public_jobs_portal.png` (/jobs), `51_public_job_page.png` (job page), `52_public_job_application_webform.png` (form, English), `53_public_job_application_webform_arabic.png` (form with `?_lang=ar`, RTL).

## Published openings (`Job Opening.publish = 1`)

| ID | Job title | Status | Route | Application web form route (`job_application_route`) | Closes on |
|---|---|---|---|---|---|
| HR-OPN-2026-0004 | Analyst | Open | `jobs/contracting_eg/analyst` | empty (default form used) | 2026-02-28 (past) |
| HR-OPN-2026-0006 | Customer Service Representative | Open | `jobs/contracting_eg/customer-service-representative` | empty | 2026-03-03 (past) |

Both are past their closing date and still Open because the scheduler (which runs `close_expired_job_openings` daily) is disabled. One of them has no description → the public page shows only the header facts.

## Public pages

- `/jobs` ("Job Openings", standard hrms portal): filters Company, Department, Employment Type, Location, Posting Date; cards show title, company, age, employment type, location, department, "Applications received: N" (because `publish_applications_received` = 1), "Closes on". No search box, no language switcher; page is LTR English for this session. The IDO Chat widget is injected on public pages.
- `/jobs/<company>/<slug>` (`51_public_job_page.png`): title, company, posted-ago, **Apply Now** (twice: top and bottom), LOCATION, DEPARTMENT, EMPLOYMENT TYPE, APPLICATIONS RECEIVED, CLOSES ON, then the description (empty for this opening). Salary range hidden (`publish_salary_range` = 0 on all openings).
- Apply Now → `/job_application/new?job_title=<Job Opening ID>`.

## Web Form record `job-application`

| Property | Value |
|---|---|
| title / doc_type / route | Job Application / **Job Applicant** / `job_application` |
| published | 1 |
| is_standard / module | 1 / HR (shipped by hrms; not customised: `client_script` is the standard 648-char script, `custom_css` empty, `introduction_text` empty, `condition_json` `[]`) |
| login_required | **0** (anonymous applicants; docs are created with owner Guest) |
| anonymous | 0 (the field is a v15+ flag for anonymised submissions; not set) |
| allow_multiple / allow_edit / allow_delete / allow_incomplete / allow_print | 0 / 0 / 0 / 0 / 0 |
| apply_document_permissions | 0 |
| allow_comments | 1 |
| show_attachments | 0 |
| max_attachment_size | 0 → framework default |
| success_url / success_message | `/jobs` / "Thank you for applying." |
| button label | default ("Submit"; Arabic "تسجيل") |
| client script (standard) | on load, reads `?job_title=` from the URL, fetches `Job Opening.job_title` with `frappe.client.get_value` and shows it in the read-only "Job Opening" field; validates `resume_link` is a URL (msgprint "Resume link not valid"). |

### Fields as rendered (DOM + `frappe.web_form.fields_dict`)

| # | fieldname | Label (en) | Label (ar) | Type on web | Mandatory | Options / notes |
|---|---|---|---|---|---|---|
| 1 | `job_title` | Job Opening | الشاغر الوظيفي | Data, **read only** | no | prefilled from `?job_title=` (shows the opening title; stores the ID) |
| 2 | `applicant_name` | Full Name | الاسم الكامل | Data | **yes** | |
| 3 | `email_id` | Email Address | البريد الإلكتروني | Data (Email) | **yes** | |
| 4 | `phone_number` | Phone Number | رقم الهاتف | Data (Phone) | no | |
| 5 | `country` | Country of Residence | بلد الإقامة | Autocomplete (Link → Country, all ~250 countries) | no | **residence, not nationality** |
| 6 | `source` | Source | المصدر | Autocomplete (Link → Job Applicant Source) | no | Outsource, Recommendation, Linkedin, Campaign, Employee Referral, Walk In, Website Listing |
| 7 | `cover_letter` | Cover Letter | خطاب التقديم | Text (textarea) | no | |
| 8 | `resume_link` | Resume Link | رابط السيرة الذاتية | Data | no | URL validated client-side |
| 9 | `resume_attachment` | Resume Attachment | مرفق السيرة الذاتية | **Attach** (button "Attach" / "إرفاق"; file browser disabled) | no | **one file**, no `accept` restriction in the DOM (any type), size limited by site default |
| — | section | Expected Salary Range per month | | Section Break | | |
| 10 | `currency` | Currency | العملة | Autocomplete (Link → Currency, ~160 codes) | no | |
| 11 | `lower_range` | Lower Range | النطاق الأدنى | Currency | no | |
| 12 | `upper_range` | Upper Range | النطاق الأعلى | Currency | no | |

Buttons: Discard / Submit (تجاهل / تسجيل). Help texts: none. Attachments beyond the single resume: none (no `show_attachments`, no photo field, no certificates field).

Fields of Job Applicant that are **not** in the web form: `designation` (fetched from opening), `status`, `applicant_rating`, `notes`, `source_name`, `employee_referral`.

### What the form does NOT capture (vs. client requirements)

nationality · national ID · date of birth · age · gender · height · weight · personal photo · certificates (multiple files) · education · experience · skills · consent/declaration. See 08_gap_analysis.md.

## Language / RTL on the public form

`?_lang=ar` renders the same form in Arabic with `html dir="rtl"` and translated labels/buttons (verified, screenshot 53). There is no visible language toggle on the public pages, so Arabic applicants depend on browser/Guest language settings or a link that carries `_lang=ar`.

## Duplicate handling

`Job Opening.prevent_duplicate_applicant` is 0 on all 5 openings, so the same e-mail can apply to the same opening more than once. Existing Job Applicant records are named by e-mail (legacy), new ones will be `HR-APP-YYYY-#####`.
