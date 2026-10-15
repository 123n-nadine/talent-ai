# Job Opening

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `HR-OPN-.YYYY.-.####` · title field: `job_title` · web view: 1 (route `None`)

Record count: see 07_data_profile.md. Fill rates below come from the 5 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | *job_details_section* | **** | _Section Break_ | | | | | | | | | | | | |
| 2 | `job_opening_template` | Job Opening Template | Link | -> Job Opening Template |  |  |  |  |  |  |  |  |  | 0 |  |
| 3 | `job_title` | Job Title | Data |  | 1 |  |  | 1 |  |  |  |  |  | 100 |  |
| 4 | `designation` | Designation | Link | -> Designation | 1 |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 5 | *column_break_5* | **** | _Column Break_ | | | | | | | | | | | | |
| 6 | `status` | Status | Select | Open<br>Closed |  | 1 |  | 1 | 1 |  |  |  |  | 100 |  |
| 7 | `posted_on` | Posted On | Datetime |  |  |  |  |  |  |  |  | Now |  | 100 |  |
| 8 | `closes_on` | Closes On | Date |  |  |  |  |  |  | eval:doc.status == 'Open' |  |  |  | 60 | If set, the job opening will be closed automatically after this date |
| 9 | `closed_on` | Closed On | Date |  |  |  |  |  |  | eval:doc.status == 'Closed' |  |  |  | 0 |  |
| 10 | *section_break_nngy* | **Company Details** | _Section Break_ | | | | | | | | | | | | |
| 11 | `company` | Company | Link | -> Company | 1 |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 12 | `department` | Department | Link | -> Department |  |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 13 | *column_break_dxpv* | **** | _Column Break_ | | | | | | | | | | | | |
| 14 | `employment_type` | Employment Type | Link | -> Employment Type |  |  |  | 1 | 1 |  |  |  |  | 100 |  |
| 15 | `location` | Location | Link | -> Branch |  |  |  |  |  |  |  |  |  | 80 |  |
| 16 | *references_section* | **References** | _Section Break_ | | | | | | | | | | | | |
| 17 | `staffing_plan` | Staffing Plan | Link | -> Staffing Plan |  |  |  |  |  |  |  |  |  | 40 |  |
| 18 | `planned_vacancies` | Planned number of Positions | Int |  |  |  | 1 |  |  | staffing_plan |  |  |  | 100 |  |
| 19 | `job_requisition` | Job Requisition | Link | -> Job Requisition |  |  | 1 |  |  |  |  |  |  | 0 |  |
| 20 | `vacancies` | Vacancies | Int |  |  |  |  |  |  |  | job_requisition.no_of_positions |  |  | 100 |  |
| 21 | *section_break_6* | **** | _Section Break_ | | | | | | | | | | | | |
| 22 | `publish` | Publish on website | Check |  |  |  |  | 1 | 1 |  |  | 0 |  | 100 |  |
| 23 | `prevent_duplicate_applicant` | Prevent Duplicate Applications | Check |  |  |  |  |  |  | publish |  | 0 |  | 100 | If enabled, candidates who have already applied with the same email address will not be allowed to apply again |
| 24 | `route` | Route | Data |  |  |  |  |  |  | publish |  |  |  | 100 |  |
| 25 | `publish_applications_received` | Publish Applications Received | Check |  |  |  |  |  |  | publish |  | 1 |  | 100 | If enabled, the total no. of applications received for this opening will be displayed on the website |
| 26 | *column_break_12* | **** | _Column Break_ | | | | | | | | | | | | |
| 27 | `job_application_route` | Application Web Form Route | Data |  |  |  |  |  |  | publish |  |  |  | 0 | Route to the custom Job Application Webform |
| 28 | *section_break_14* | **** | _Section Break_ | | | | | | | | | | | | |
| 29 | `description` | Description | Text Editor |  |  |  |  | 1 |  |  |  |  |  | 60 | Job profile, qualifications required etc. |
| 30 | *pay_details_tab* | **Pay Details** | _Tab Break_ | | | | | | | | | | | | |
| 31 | `currency` | Currency | Link | -> Currency |  |  |  |  |  |  |  |  |  | 100 |  |
| 32 | `lower_range` | Lower Range | Currency | currency |  |  |  |  |  |  |  |  |  | 100 |  |
| 33 | `upper_range` | Upper Range | Currency | currency |  |  |  |  |  |  |  |  |  | 100 |  |
| 34 | *column_break_pfir* | **** | _Column Break_ | | | | | | | | | | | | |
| 35 | `salary_per` | Salary Paid Per | Select | Month<br>Year |  |  |  |  |  |  |  | Month |  | 100 |  |
| 36 | `publish_salary_range` | Publish Salary Range | Check |  |  |  |  |  |  |  |  | 0 |  | 100 |  |

## States (list indicators)

- Open (Green)
- Closed (Gray)

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| HR User | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

- Custom Fields: none

### Property Setters

| name | field | property | value | module | created |
|---|---|---|---|---|---|
| Job Opening-staffing_plan-read_only | `staffing_plan` | read_only | `0` | IDO Desk | 2026-10-04 |
| Job Opening-vacancies-depends_on | `vacancies` | depends_on | `` | IDO Desk | 2026-10-04 |
| Job Opening-vacancies-read_only | `vacancies` | read_only | `0` | IDO Desk | 2026-10-04 |
| Job Opening-vacancies-read_only_depends_on | `vacancies` | read_only_depends_on | `eval:doc.job_requisition` | IDO Desk | 2026-10-04 |
| Job Opening-vacancies-reqd | `vacancies` | reqd | `0` | IDO Desk | 2026-10-04 |
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 38 chars (empty wrapper only)
- App-level UI injection by `ido_design` (IDO Desk kit, `idk.bundle.js`): see 02_navigation_map.md, section 'Client-specific UI'.
