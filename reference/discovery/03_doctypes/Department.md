# Department

Module: **Setup** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `-` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `department_name` | Department | Data |  | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 2 | `parent_department` | Parent Department | Link | -> Department |  |  |  | 1 |  |  |  |  |  |  |  |
| 3 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 4 | `company` | Company | Link | -> Company | 1 |  |  |  | 1 |  |  |  |  |  |  |
| 5 | `is_group` | Is Group | Check |  |  |  |  | 1 |  |  |  | 0 |  |  |  |
| 6 | `disabled` | Disabled | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 7 | `lft` | lft | Int |  |  | 1 | 1 |  |  |  |  |  |  |  |  |
| 8 | `rgt` | rgt | Int |  |  | 1 | 1 |  |  |  |  |  |  |  |  |
| 9 | `old_parent` | Old Parent | Data |  |  | 1 |  |  |  |  |  |  |  |  |  |
| 10 | *section_break_4* | **** | _Section Break_ | | | | | | | | | | | | |
| 11 | `payroll_cost_center` | Payroll Cost Center | Link | -> Cost Center |  |  |  |  |  |  |  |  | YES |  |  |
| 12 | *column_break_9* | **** | _Column Break_ | | | | | | | | | | | | |
| 13 | `leave_block_list` | Leave Block List | Link | -> Leave Block List |  |  |  | 1 |  |  |  |  | YES |  | Days for which Holidays are blocked for this department. |
| 14 | *approvers* | **Approvers** | _Section Break_ | | | | | | | | | | | | |
| 15 | `shift_request_approver` | Shift Request Approver | Table | child -> **Department Approver** |  |  |  |  |  |  |  |  | YES |  |  |
| 16 | `leave_approvers` | Leave Approver | Table | child -> **Department Approver** |  |  |  |  |  |  |  |  | YES |  |  |
| 17 | `expense_approvers` | Expense Approver | Table | child -> **Department Approver** |  |  |  |  |  |  |  |  | YES |  |  |

## Child tables

- `shift_request_approver` (Table) -> **Department Approver** — see `Department_Approver.md`
- `leave_approvers` (Table) -> **Department Approver** — see `Department_Approver.md`
- `expense_approvers` (Table) -> **Department Approver** — see `Department_Approver.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 37 chars (empty wrapper only)
