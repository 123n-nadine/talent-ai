# Staffing Plan Detail

Module: **HR** · custom DocType: 0 · child table: 1 · submittable: 0 · naming: `-` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `designation` | Designation | Link | -> Designation | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 2 | `vacancies` | Vacancies | Int |  |  |  |  | 1 |  |  |  |  |  |  |  |
| 3 | `estimated_cost_per_position` | Estimated Cost Per Position | Currency | Company:company:default_currency |  |  |  | 1 |  |  |  |  |  |  |  |
| 4 | `total_estimated_cost` | Total Estimated Cost | Currency | Company:company:default_currency |  |  | 1 | 1 |  |  |  |  |  |  |  |
| 5 | *column_break_5* | **** | _Column Break_ | | | | | | | | | | | | |
| 6 | `current_count` | Current Count | Int |  |  |  | 1 |  |  |  |  |  |  |  |  |
| 7 | `current_openings` | Current Openings | Int |  |  |  | 1 |  |  |  |  |  |  |  |  |
| 8 | `number_of_positions` | Number Of Positions | Int |  |  |  | 1 | 1 |  |  |  |  |  |  |  |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
