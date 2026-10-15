# Appointment Letter

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `HR-APP-LETTER-.#####` · title field: `applicant_name`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `job_applicant` | Job Applicant | Link | -> Job Applicant | 1 |  |  |  |  |  |  |  |  |  |  |
| 2 | `applicant_name` | Applicant Name | Data |  | 1 |  | 1 | 1 |  |  | job_applicant.applicant_name |  |  |  |  |
| 3 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 4 | `company` | Company | Link | -> Company | 1 |  |  |  |  |  |  |  |  |  |  |
| 5 | `appointment_date` | Appointment Date | Date |  | 1 |  |  |  |  |  |  |  |  |  |  |
| 6 | `appointment_letter_template` | Appointment Letter Template | Link | -> Appointment Letter Template | 1 |  |  |  |  |  |  |  |  |  |  |
| 7 | *body_section* | **Body** | _Section Break_ | | | | | | | | | | | | |
| 8 | `introduction` | Introduction | Long Text |  | 1 |  |  |  |  |  | appointment_letter_template.introduction |  |  |  |  |
| 9 | `terms` | Terms | Table | child -> **Appointment Letter content** | 1 |  |  |  |  |  |  |  |  |  |  |
| 10 | `closing_notes` | Closing Notes | Text |  |  |  |  |  |  |  |  |  |  |  |  |

## Child tables

- `terms` (Table) -> **Appointment Letter content** — see `Appointment_Letter_content.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 45 chars (empty wrapper only)
