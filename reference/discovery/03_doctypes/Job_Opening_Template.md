# Job Opening Template

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `field:template_title` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `template_title` | Template Title | Data |  | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 2 | `department` | Department | Link | -> Department |  |  |  | 1 |  |  |  |  |  |  |  |
| 3 | `designation` | Designation | Link | -> Designation |  |  |  |  |  |  |  |  |  |  |  |
| 4 | *column_break_wkcr* | **** | _Column Break_ | | | | | | | | | | | | |
| 5 | `employment_type` | Employment Type | Link | -> Employment Type |  |  |  |  |  |  |  |  |  |  |  |
| 6 | `location` | Location | Link | -> Branch |  |  |  |  |  |  |  |  |  |  |  |
| 7 | *pay_details_section* | **Pay Details** | _Section Break_ | | | | | | | | | | | | |
| 8 | `currency` | Currency | Link | -> Currency |  |  |  |  |  |  |  |  |  |  |  |
| 9 | `upper_range` | Upper Range | Currency |  |  |  |  |  |  |  |  |  |  |  |  |
| 10 | `lower_range` | Lower Range | Currency |  |  |  |  |  |  |  |  |  |  |  |  |
| 11 | *column_break_vqyu* | **** | _Column Break_ | | | | | | | | | | | | |
| 12 | `salary_per` | Salary Paid Per | Select | Month<br>Year |  |  |  |  |  |  |  | Month |  |  |  |
| 13 | `publish_salary_range` | Publish Salary Range | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 14 | *section_break_dwfh* | **** | _Section Break_ | | | | | | | | | | | | |
| 15 | `description` | Description | Text Editor |  |  |  |  |  |  |  |  |  |  |  |  |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 47 chars (empty wrapper only)
