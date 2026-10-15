# 08 — Gap analysis against the client's requirements

Legend for "Status": **Exists** · **Exists but not captured in web form** · **Exists but mostly empty** · **Missing** · **Unclear**.
Evidence columns refer to fill rates in 07_data_profile.md and screenshots in `screenshots/`.

## A. Client requirements

| # | Requirement | Status | Where it lives today (`DocType.fieldname`, type) | Evidence |
|---|---|---|---|---|
| 1 | Nationality rule (Saudi only for security roles) | **Missing** on the applicant; exists only on Employee | `Job Applicant.country` (Link → Country, label "Country of Residence") is residence, not nationality. `Employee.nationality` (Link → Country, custom field from hr_ksa_customization) exists but only after hiring. No field on Job Opening / Designation to declare "Saudi only". | web form field 5 (`06_web_form.md`); `Job_Applicant.md`; `_raw_integration.json` employee fields |
| 2 | Minimum height (e.g. 180 cm) | **Missing** | No height field on Job Applicant, Job Opening, Designation or Employee. | all DocType files |
| 3 | Maximum weight (e.g. 80 kg) | **Missing** | No weight field anywhere. | idem |
| 4 | Age range | **Missing** on applicant | `Employee.date_of_birth` (Date, reqd) exists post-hire only. Job Applicant has no DOB/age; Job Opening has no min/max age. | idem |
| 5 | National ID | **Missing** on applicant | `Employee.passport_number` exists; HR KSA app adds GOSI number and Arabic names on Employee, but no national ID / Iqama on Job Applicant. `Identification Document Type` master exists (HR module) but is not linked from recruitment. | `_raw_integration.json` |
| 6 | Date of birth | **Missing** on applicant | see 4 | |
| 7 | Job description (1–50 lines) | **Exists, mostly empty** | `Job Opening.description` (Text Editor, shown on the public page); `Job Opening Template.description`; `Job Requisition.description` (fetched from `Designation.description`, Text). | fill 60 % on openings (2 of 5 empty, one of them published); 0 of 34 designations have a description; 0 templates; kit flags "published with no description" as a hard readiness failure (`21_job_opening_form.png`) |
| 8 | Competencies / skills / qualifications per job | **Exists but empty** (structure only) | `Designation.skills` → child `Designation Skill.skill` (Link → `Skill`, custom field installed by hrms); `Interview Type.expected_skill_set` → `Expected Skill Set.skill`; `Interview Feedback.skill_assessment` → `Skill Assessment (skill, rating)`. Nothing on Job Opening itself; no proficiency level, no "mandatory vs nice-to-have", no qualification/certificate master. | Skill master has 1 test record ("Good Search"); Interview Type has no skills; Designation forms show no rows |
| 9 | Applicant attachments: CV | **Exists** (single file) | `Job Applicant.resume_attachment` (Attach, one file, any type) + `Job Applicant.resume_link` (Data URL); desk form has "Open Resume in New Tab" and a hidden PDF preview (`resume_preview_html`, `open_resume_button`). Web form exposes both. | fill 0 % on both; 0 résumé files on the site (`07_data_profile.md`) |
| 10 | Applicant attachments: personal photo | **Missing** as a field | No `Attach Image` on Job Applicant (DocType has no `image_field`); `Employee.image` exists post-hire. The one file on the site is a jpg sidebar attachment on an applicant, i.e. HR attached a photo manually via the sidebar. | File aggregate: 1 jpg, attached_to_field empty |
| 11 | Applicant attachments: certificates (multiple) | **Missing** as a field | Only sidebar attachments (desk users) — not available on the web form (`show_attachments` = 0, `max_attachments` not set). | Web Form record |
| 12 | Keep all applicants (talent pool) even if they applied for another job | **Exists** | `Job Applicant.job_title` is optional; applicants are never deleted automatically; status values Open/Replied/Shortlisted/Rejected/Hold/Accepted keep the record; the kit's Candidates board lists per opening. No "talent pool" tag, no "re-matched to opening" field, no multi-opening table (one applicant = one opening at a time). | 1 of 5 applicants has no opening; `Job_Applicant.md` |
| 13 | HR filters Job Applicants with many list filters | **Exists** (ad-hoc) | List view: standard filters `job_title`, `status`, `applicant_rating` (+ ID, Full Name); any field filterable via "Filters"; Report View; Kanban replaced by the kit's Hiring pipeline. **No saved List Filters, no List View Settings, no user list settings** on this demo. Filtering on nationality/age/height/weight is impossible because the fields do not exist. | `_raw_integration.json` saved_list_filters = [] ; `10_job_applicant_list.png` |

## B. Related findings that affect the design

| Topic | Finding |
|---|---|
| Hard-eligibility rule definition per job | No place to store rules. Candidates: custom fields on **Job Opening** (and/or Job Opening Template) such as `required_nationality`, `min_height_cm`, `max_weight_kg`, `min_age`, `max_age`, `gender` — or a dedicated child table "Eligibility Rule" (field, operator, value, hard/soft). |
| Where AI output could be stored | `Job Applicant.applicant_rating` (Rating 0–5, 0 on all records) is the only existing score slot; `notes` (Data, 140 chars) is too small for a summary. No "AI score", "AI rank", "screening result", "parsed CV JSON", "eligibility result" fields exist. |
| Scheduler | Disabled on the demo (`enable_scheduler` = 0). Any AI layer that relies on `after_insert` hooks + background jobs (enqueue) will not run here; on production this must be confirmed. |
| Webhooks / Server Scripts | **0 Webhooks**, 0 Server Scripts, 0 Client Scripts, 0 Notifications, 0 Assignment Rules on recruitment DocTypes → integration must be added (Webhook on `Job Applicant` after_insert/on_update is the least invasive). |
| Duplicate applicants | `prevent_duplicate_applicant` off; existing records keyed by e-mail; new ones by series. Dedupe for a talent pool must be designed (e-mail + phone + national ID). |
| Public form language | Arabic works only with `?_lang=ar`; no toggle. Security-guard applicants are likely Arabic-first. |
| Attachments from Guest | Web form upload works for a single résumé; multiple files (photo, certificates) need either extra Attach fields on Job Applicant exposed in the web form (one file each) or a child table with Attach (web forms support child tables with Attach in v15+, must be verified in v16). |
| Existing custom app | `ido_design` (IDO Desk kit) already injects read-only "readiness" and "candidate" panels via `hr_gaps.api.*`. An AI screening result could be surfaced the same way, but that app is shared across clients. |
| Competencies | Skill/Designation Skill exist but are empty; Interview Feedback scoring per skill exists. If skills are maintained on Designation, the AI layer can read them via `Designation.skills`. |
| Designations for security roles | Designation list contains Arabic security roles ("فرد امن", "مدير قسم الامن"), confirming the client's domain, but these have no description or skills. |

## C. Fields an AI screening layer needs that do not exist yet (proposal only — nothing was created)

### On Job Opening (or Job Opening Template) — "what to screen for"

| Proposed field | Type | Role | Rationale |
|---|---|---|---|
| `required_nationality` | Link → Country (or Table MultiSelect) | hard_filter | "Saudi only" for security roles |
| `min_age` / `max_age` | Int | hard_filter | age range |
| `min_height_cm` / `max_weight_kg` | Int | hard_filter | physical requirements |
| `required_gender` | Link → Gender / Select | hard_filter | if applicable |
| `required_education_level` | Select / Link | hard_filter or soft | |
| `min_years_experience` | Int | soft_criterion | |
| `required_skills` | Table (Skill, weight, mandatory ☐) | soft_criterion | reuse `Skill`; Designation.skills can seed it |
| `required_certificates` | Table (Certificate Type, mandatory ☐) | hard/soft | security licences, first aid, etc. |
| `screening_rubric` | Long Text / JSON | semantic_text | free-form instruction for the LLM |
| `eligibility_rules` (alternative) | Table (field, operator, value, hard ☐) | hard_filter | generic rule table instead of fixed fields |

### On Job Applicant — "facts about the candidate" (to be collected in the web form)

| Proposed field | Type | Role | Rationale |
|---|---|---|---|
| `nationality` | Link → Country | hard_filter | distinct from `country` (residence) |
| `national_id` / `id_type` | Data + Link → Identification Document Type | metadata / hard_filter | uniqueness + Saudi/Iqama distinction; sensitive, restrict permlevel |
| `date_of_birth` | Date | hard_filter (age) | |
| `gender` | Link → Gender | hard_filter | |
| `height_cm`, `weight_kg` | Int / Float | hard_filter | self-declared, verified at interview |
| `photo` | Attach Image | attachment | set as `image_field` |
| `certificates` | Table (title, Attach) | attachment | multiple files |
| `education` / `experience` | Table or Long Text | semantic_text | parsed from CV or entered |
| `skills` | Table (Skill) | soft_criterion | parsed or self-declared |
| `years_of_experience` | Float | soft_criterion | |
| `arabic_name` | Data | metadata | HR KSA already keeps Arabic names on Employee |
| `consent_data_processing` | Check | metadata | PDPL |

### On Job Applicant — "AI output" (written by the AI layer, read by HR)

| Proposed field | Type | Role |
|---|---|---|
| `ai_eligibility` | Select (Eligible / Not eligible / Needs review) + `ai_eligibility_reasons` (Small Text) | result of hard filters |
| `ai_score` (0–100) / `ai_rank` (per opening) | Float / Int | ranking |
| `ai_summary` | Long Text | 5-line CV summary |
| `ai_parsed_cv` | JSON / Code (hidden) | structured extraction (education, experience, skills, languages) |
| `ai_matched_skills` / `ai_missing_skills` | Table or Small Text | explainability |
| `ai_model`, `ai_scored_on`, `ai_input_hash` | Data / Datetime / Data | audit & re-scoring |
| `talent_pool_matches` | Table (Job Opening, score) | re-use of applicants for other openings |
| `hr_override` + `hr_override_reason` | Check + Small Text | human-in-the-loop |

Where to put them: Custom Fields (via a small custom app or Customize Form) on Job Applicant / Job Opening, plus exposure of the applicant-side fields in a **copy** of the `job-application` Web Form (do not edit the standard one), plus a Webhook or `after_insert` hook to trigger scoring. None of this was created in this discovery.
