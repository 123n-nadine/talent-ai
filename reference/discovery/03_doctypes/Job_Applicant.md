# Job Applicant

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `HR-APP-.YYYY.-.#####` · title field: `applicant_name`

Record count: see 07_data_profile.md. Fill rates below come from the 5 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | *details_section* | **Details** | _Section Break_ | | | | | | | | | | | | |
| 2 | `applicant_name` | Full Name | Data |  | 1 |  |  |  |  |  |  |  |  | 100 |  |
| 3 | `email_id` | Email Address | Data | Email | 1 |  |  |  |  |  |  |  |  | 100 |  |
| 4 | `phone_number` | Phone Number | Data | Phone |  |  |  |  |  |  |  |  |  | 60 |  |
| 5 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 6 | `job_title` | Job Opening | Link | -> Job Opening |  |  |  | 1 |  |  |  |  |  | 80 |  |
| 7 | `designation` | Designation | Link | -> Designation |  |  |  |  |  |  | job_title.designation |  |  | 80 |  |
| 8 | `country` | Country | Link | -> Country |  |  |  |  |  |  |  |  |  | 100 |  |
| 9 | *column_break_enue* | **** | _Column Break_ | | | | | | | | | | | | |
| 10 | `status` | Status | Select | Open<br>Replied<br>Shortlisted<br>Rejected<br>Hold<br>Accepted | 1 |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 11 | `applicant_rating` | Applicant Rating | Rating |  |  |  |  | 1 |  |  |  |  |  | 100 |  |
| 12 | *section_break_6* | **Resume** | _Section Break_ | | | | | | | | | | | | |
| 13 | `resume_link` | Link | Data |  |  |  |  |  |  |  |  |  |  | 0 |  |
| 14 | `resume_preview_html` | Preview | HTML |  |  | 1 |  |  |  |  |  |  |  |  |  |
| 15 | `open_resume_button` | Open Resume in New Tab | Button |  |  | 1 |  |  |  |  |  |  |  |  |  |
| 16 | `cover_letter` | Cover Letter | Text |  |  |  |  |  |  |  |  |  |  | 0 |  |
| 17 | `resume_attachment` | Attachment | Attach |  |  |  |  |  |  |  |  |  |  | 0 |  |
| 18 | `notes` | Notes | Data |  |  |  | 1 |  |  |  |  |  |  | 0 |  |
| 19 | *source_and_rating_section* | **Source** | _Section Break_ | | | | | | | | | | | | |
| 20 | `source` | Source | Link | -> Job Applicant Source |  |  |  |  |  |  |  |  |  | 40 |  |
| 21 | `source_name` | Source Name | Link | -> Employee |  |  |  |  |  | eval: doc.source=="Employee Referral"  |  |  |  | 20 |  |
| 22 | *column_break_13* | **** | _Column Break_ | | | | | | | | | | | | |
| 23 | `employee_referral` | Employee Referral | Link | -> Employee Referral |  |  | 1 |  |  |  |  |  |  | 0 |  |
| 24 | *salary_expectation_tab* | **Salary Expectation** | _Tab Break_ | | | | | | | | | | | | |
| 25 | `currency` | Currency | Link | -> Currency |  |  |  |  |  |  |  |  |  | 80 |  |
| 26 | *column_break_18* | **** | _Column Break_ | | | | | | | | | | | | |
| 27 | `lower_range` | Lower Range | Currency | currency |  |  |  |  |  |  |  |  |  | 100 |  |
| 28 | `upper_range` | Upper Range | Currency | currency |  |  |  |  |  |  |  |  |  | 100 |  |

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| HR User | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| Employee Self Service | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 40 chars (empty wrapper only)
- App-level UI injection by `ido_design` (IDO Desk kit, `idk.bundle.js`): see 02_navigation_map.md, section 'Client-specific UI'.
