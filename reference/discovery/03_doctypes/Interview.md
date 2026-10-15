# Interview

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 1 · naming: `HR-INT-.YYYY.-.####` · title field: `job_applicant`

Record count: see 07_data_profile.md. Fill rates below come from the 2 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | *interview_details_section* | **Details** | _Section Break_ | | | | | | | | | | | | |
| 2 | `interview_type` | Interview Type | Link | -> Interview Type | 1 |  |  | 1 | 1 |  |  |  |  | 0 |  |
| 3 | `job_applicant` | Job Applicant | Link | -> Job Applicant | 1 |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 4 | `job_opening` | Job Opening | Link | -> Job Opening |  |  | 1 |  |  |  | job_applicant.job_title |  |  | 100 |  |
| 5 | `designation` | Designation | Link | -> Designation |  |  | 1 | 1 | 1 |  | interview_type.designation |  |  | 100 |  |
| 6 | `resume_link` | Resume link | Data |  |  |  |  |  |  |  | job_applicant.resume_link |  |  | 0 |  |
| 7 | *column_break_4* | **** | _Column Break_ | | | | | | | | | | | | |
| 8 | `status` | Status | Select | Pending<br>Under Review<br>Cleared<br>Rejected<br>Cancelled | 1 |  |  | 1 | 1 |  |  | Pending |  | 100 |  |
| 9 | `scheduled_on` | Scheduled On | Date |  | 1 |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 10 | `from_time` | From Time | Time |  | 1 |  |  | 1 |  |  |  |  |  | 100 |  |
| 11 | `to_time` | To Time | Time |  | 1 |  |  | 1 |  |  |  |  |  | 100 |  |
| 12 | *section_break_hqvh* | **** | _Section Break_ | | | | | | | | | | | | |
| 13 | `interview_details` | Interviewers | Table | child -> **Interview Detail** |  |  |  |  |  |  |  |  |  |  |  |
| 14 | *ratings_section* | **Ratings** | _Section Break_ | | | | | | | | | | | | |
| 15 | `expected_average_rating` | Expected Average Rating | Rating |  |  |  | 1 |  |  |  | interview_type.expected_average_rating |  |  | 100 |  |
| 16 | *column_break_12* | **** | _Column Break_ | | | | | | | | | | | | |
| 17 | `average_rating` | Obtained Average Rating | Rating |  |  |  | 1 | 1 |  |  |  |  |  | 100 |  |
| 18 | *section_break_13* | **Interview Summary** | _Section Break_ | | | | | | | | | | | | |
| 19 | `interview_summary` |  | Text |  |  |  |  |  |  |  |  |  |  | 0 |  |
| 20 | `reminded` | Reminded | Check |  |  | 1 |  |  |  |  |  | 0 |  |  |  |
| 21 | `amended_from` | Amended From | Link | -> Interview |  |  | 1 |  |  |  |  |  |  |  |  |
| 22 | *feedback_tab* | **Feedback** | _Tab Break_ | | | | | | | | | | | | |
| 23 | `feedback_html` | Feedback HTML | HTML |  |  |  |  |  |  |  |  |  |  |  |  |

## Child tables

- `interview_details` (Table) -> **Interview Detail** — see `Interview_Detail.md`

## Connections (DocType Links shown in the form dashboard)

- Interview Feedback via `interview`

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| System Manager | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| HR Manager | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Interviewer | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| HR User | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 36 chars (empty wrapper only)
- App-level UI injection by `ido_design` (IDO Desk kit, `idk.bundle.js`): see 02_navigation_map.md, section 'Client-specific UI'.
