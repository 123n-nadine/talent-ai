# Interview Feedback

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 1 · naming: `HR-INT-FEED-.####` · title field: `interviewer`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | *details_section* | **Details** | _Section Break_ | | | | | | | | | | | | |
| 2 | `interview` | Interview | Link | -> Interview | 1 |  |  | 1 | 1 |  |  |  |  |  |  |
| 3 | `interview_type` | Interview Type | Link | -> Interview Type | 1 |  | 1 | 1 | 1 |  | interview.interview_type |  |  |  |  |
| 4 | `job_applicant` | Job Applicant | Link | -> Job Applicant |  |  | 1 | 1 | 1 |  | interview.job_applicant |  |  |  |  |
| 5 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 6 | `interviewer` | Interviewer | Link | -> User | 1 |  |  | 1 | 1 |  |  |  |  |  |  |
| 7 | `result` | Result | Select | <br>Cleared<br>Rejected | 1 |  |  | 1 | 1 |  |  |  |  |  |  |
| 8 | *section_break_4* | **Skill Assessment** | _Section Break_ | | | | | | | | | | | | |
| 9 | `skill_assessment` |  | Table | child -> **Skill Assessment** | 1 |  |  |  |  |  |  |  |  |  |  |
| 10 | `average_rating` | Average Rating | Rating |  |  |  | 1 | 1 |  |  |  |  |  |  |  |
| 11 | *section_break_7* | **Feedback** | _Section Break_ | | | | | | | | | | | | |
| 12 | `feedback` |  | Text |  |  |  |  |  |  |  |  |  |  |  |  |
| 13 | `amended_from` | Amended From | Link | -> Interview Feedback |  |  | 1 |  |  |  |  |  |  |  |  |

## Child tables

- `skill_assessment` (Table) -> **Skill Assessment** — see `Skill_Assessment.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 45 chars (empty wrapper only)
