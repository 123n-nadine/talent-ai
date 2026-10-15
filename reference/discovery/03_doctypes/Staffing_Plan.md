# Staffing Plan

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 1 · naming: `prompt` · title field: `-`

Record count: see 07_data_profile.md. Fill rates below come from the 2 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `company` | Company | Link | -> Company | 1 |  |  | 1 |  |  |  |  |  | 100 |  |
| 2 | `department` | Department | Link | -> Department |  |  |  |  |  |  |  |  |  | 100 |  |
| 3 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 4 | `from_date` | From Date | Date |  | 1 |  |  |  |  |  |  |  |  | 100 |  |
| 5 | `to_date` | To Date | Date |  | 1 |  |  |  |  |  |  |  |  | 100 |  |
| 6 | *staffing_plan_details* | **Details** | _Section Break_ | | | | | | | | | | | | |
| 7 | `get_job_requisitions` | Get Job Requisitions | Button |  |  |  |  |  |  |  |  |  |  |  |  |
| 8 | `staffing_details` | Staffing Details | Table | child -> **Staffing Plan Detail** | 1 |  |  |  |  |  |  |  |  |  |  |
| 9 | *section_break_8* | **** | _Section Break_ | | | | | | | | | | | | |
| 10 | `total_estimated_budget` | Total Estimated Budget | Currency | Company:company:default_currency |  |  | 1 |  |  |  |  | 0.00 |  | 100 |  |
| 11 | `amended_from` | Amended From | Link | -> Staffing Plan |  |  | 1 |  |  |  |  |  |  |  |  |

## Child tables

- `staffing_details` (Table) -> **Staffing Plan Detail** — see `Staffing_Plan_Detail.md`

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| HR Manager | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| HR User | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 40 chars (empty wrapper only)
- App-level UI injection by `ido_design` (IDO Desk kit, `idk.bundle.js`): see 02_navigation_map.md, section 'Client-specific UI'.
