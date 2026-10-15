# Designation

Module: **Setup** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `field:designation_name` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `designation_name` | Designation | Data |  | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 2 | `description` | Description | Text |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | `appraisal_template` | Appraisal Template | Link | -> Appraisal Template |  |  |  |  |  |  |  |  | YES |  |  |
| 4 | *required_skills_section* | **Required Skills** | _Section Break_ | | | | | | | | | | | | |
| 5 | `skills` | Skills | Table | child -> **Designation Skill** |  |  |  |  |  |  |  |  | YES |  |  |

## Child tables

- `skills` (Table) -> **Designation Skill** — see `Designation_Skill.md`

## Customizations

### Custom Fields

| name | fieldname | label | type | options | insert_after | module | created |
|---|---|---|---|---|---|---|---|
| Designation-appraisal_template | `appraisal_template` | Appraisal Template | Link | Appraisal Template | description | - | 2025-04-23 |
| Designation-required_skills_section | `required_skills_section` | Required Skills | Section Break |  | appraisal_template | - | 2025-04-23 |
| Designation-skills | `skills` | Skills | Table | Designation Skill | required_skills_section | - | 2025-04-23 |
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 38 chars (empty wrapper only)
