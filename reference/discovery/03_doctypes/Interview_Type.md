# Interview Type

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `field:interview_type_name` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `interview_type_name` | Interview Type Name | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | `interviewers` | Interviewers | Table MultiSelect | child -> **Interviewer** |  |  |  |  |  |  |  |  |  |  |  |
| 3 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 4 | `expected_average_rating` | Expected Average Rating | Rating |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 | *expected_skills_section* | **** | _Section Break_ | | | | | | | | | | | | |
| 6 | `designation` | Designation | Link | -> Designation |  |  |  |  |  |  |  |  |  |  |  |
| 7 | `expected_skill_set` | Expected Skillset | Table | child -> **Expected Skill Set** | 1 |  |  |  |  |  |  |  |  |  |  |
| 8 | *section_break_xlzv* | **** | _Section Break_ | | | | | | | | | | | | |
| 9 | `description` | Description | Text |  |  |  |  |  |  |  |  |  |  |  |  |

## Child tables

- `interviewers` (Table MultiSelect) -> **Interviewer** — see `Interviewer.md`
- `expected_skill_set` (Table) -> **Expected Skill Set** — see `Expected_Skill_Set.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 41 chars (empty wrapper only)
