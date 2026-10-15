# Job Requisition

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `naming_series:` · title field: `designation`

Record count: see 07_data_profile.md. Fill rates below come from the 0 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `naming_series` | Naming Series | Select | HR-HIREQ- |  |  |  |  |  |  |  |  |  |  |  |
| 2 | `designation` | Designation | Link | -> Designation | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 3 | `staffing_plan` | Workforce Plan | Link | -> Staffing Plan |  |  |  |  |  |  |  |  | YES |  |  |
| 4 | `plan_seats_left` | Seats Left in the Plan | Int |  |  |  | 1 |  |  |  |  |  | YES |  |  |
| 5 | `department` | Department | Link | -> Department |  |  |  |  |  |  |  |  |  |  |  |
| 6 | *column_break_qkna* | **** | _Column Break_ | | | | | | | | | | | | |
| 7 | `plan_over_notice` | This request asks for more than the plan has left. | HTML |  |  |  |  |  |  |  |  |  | YES |  |  |
| 8 | `no_of_positions` | No of. Positions | Int |  | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 9 | `expected_compensation` | Expected Compensation | Currency | Company:company:default_currency | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 10 | *column_break_4* | **** | _Column Break_ | | | | | | | | | | | | |
| 11 | `company` | Company | Link | -> Company | 1 |  |  |  |  |  |  |  |  |  |  |
| 12 | `status` | Status | Select | Pending<br>Open & Approved<br>Rejected<br>Filled<br>On Hold<br>Cancelled | 1 |  |  | 1 |  |  |  |  |  |  |  |
| 13 | *section_break_7* | **Requested By** | _Section Break_ | | | | | | | | | | | | |
| 14 | `requested_by` | Requested By | Link | -> Employee | 1 |  |  |  | 1 |  |  |  |  |  |  |
| 15 | `requested_by_name` | Requested By (Name) | Data |  |  |  | 1 | 1 |  |  | requested_by.employee_name |  |  |  |  |
| 16 | *column_break_10* | **** | _Column Break_ | | | | | | | | | | | | |
| 17 | `requested_by_dept` | Department | Link | -> Department |  |  | 1 |  |  |  | requested_by.department |  |  |  |  |
| 18 | `requested_by_designation` | Designation | Link | -> Designation |  |  | 1 |  |  |  | requested_by.designation |  |  |  |  |
| 19 | *timelines_tab* | **Timelines** | _Section Break_ | | | | | | | | | | | | |
| 20 | `posting_date` | Posting Date | Date |  | 1 |  |  |  |  |  |  | Today |  |  |  |
| 21 | `completed_on` | Completed On | Date |  |  |  |  |  |  | eval:doc.status=="Filled" |  |  |  |  |  |
| 22 | *column_break_15* | **** | _Column Break_ | | | | | | | | | | | | |
| 23 | `expected_by` | Expected By | Date |  |  |  |  | 1 |  |  |  |  |  |  |  |
| 24 | `time_to_fill` | Time to Fill | Duration |  |  |  | 1 |  |  |  |  |  |  |  | Time taken to fill the open positions |
| 25 | *job_description_tab* | **Job Description** | _Tab Break_ | | | | | | | | | | | | |
| 26 | `description` | Job Description | Text Editor |  | 1 |  |  |  |  |  | designation.description |  |  |  |  |
| 27 | `reason_for_requesting` | Reason for Requesting | Text |  |  |  |  |  |  |  |  |  |  |  |  |
| 28 | *connections_tab* | **Connections** | _Tab Break_ | | | | | | | | | | | | |

## Connections (DocType Links shown in the form dashboard)

- Job Opening via `job_requisition`

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| System Manager | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

### Custom Fields

| name | fieldname | label | type | options | insert_after | module | created |
|---|---|---|---|---|---|---|---|
| Job Requisition-plan_over_notice | `plan_over_notice` | This request asks for more than the plan has left. | HTML |  | column_break_qkna | IDO Desk | 2026-10-04 |
| Job Requisition-plan_seats_left | `plan_seats_left` | Seats Left in the Plan | Int |  | staffing_plan | IDO Desk | 2026-10-04 |
| Job Requisition-staffing_plan | `staffing_plan` | Workforce Plan | Link | Staffing Plan | designation | IDO Desk | 2026-10-04 |
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 42 chars (empty wrapper only)
- App-level UI injection by `ido_design` (IDO Desk kit, `idk.bundle.js`): see 02_navigation_map.md, section 'Client-specific UI'.
