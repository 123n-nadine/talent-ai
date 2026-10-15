# Appointment Letter Template

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `field:template_name` · title field: `template_name`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `template_name` | Template Name | Data |  | 1 |  |  |  |  |  |  |  |  |  |  |
| 2 | `introduction` | Introduction | Long Text |  | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 3 | `terms` | Terms | Table | child -> **Appointment Letter content** | 1 |  |  |  |  |  |  |  |  |  |  |
| 4 | `closing_notes` | Closing Notes | Text |  |  |  |  |  |  |  |  |  |  |  |  |

## Child tables

- `terms` (Table) -> **Appointment Letter content** — see `Appointment_Letter_content.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 54 chars (empty wrapper only)
