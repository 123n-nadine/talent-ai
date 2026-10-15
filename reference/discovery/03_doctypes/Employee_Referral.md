# Employee Referral

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 1 · naming: `format:HR-REF-{####}` · title field: `full_name`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `first_name` | First Name  | Data |  | 1 |  |  |  |  |  |  |  |  |  |  |
| 2 | `last_name` | Last Name | Data |  | 1 |  |  |  |  |  |  |  |  |  |  |
| 3 | `full_name` | Full Name | Data |  |  |  | 1 | 1 |  |  |  |  |  |  |  |
| 4 | *column_break_6* | **** | _Column Break_ | | | | | | | | | | | | |
| 5 | `date` | Date | Date |  | 1 |  |  |  | 1 |  |  |  |  |  |  |
| 6 | `status` | Status | Select | Pending<br>In Process<br>Accepted<br>Rejected<br>Cancelled | 1 |  | 1 |  | 1 |  |  |  |  |  |  |
| 7 | `for_designation` | For Designation  | Link | -> Designation | 1 |  |  | 1 | 1 |  |  |  |  |  |  |
| 8 | *referral_details_section* | **Referral Details** | _Section Break_ | | | | | | | | | | | | |
| 9 | `email` | Email | Data | Email | 1 |  |  | 1 | 1 |  |  |  |  |  |  |
| 10 | `contact_no` | Contact No. | Data | Phone |  |  |  |  | 1 |  |  |  |  |  |  |
| 11 | `resume_link` | Resume Link | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 12 | *column_break_12* | **** | _Column Break_ | | | | | | | | | | | | |
| 13 | `current_employer` | Current Employer  | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 14 | `current_job_title` | Current Job Title | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 15 | `resume` | Resume | Attach |  |  |  |  |  |  |  |  |  |  |  |  |
| 16 | *referrer_details_section* | **Referrer Details** | _Section Break_ | | | | | | | | | | | | |
| 17 | `referrer` | Referrer | Link | -> Employee | 1 |  |  |  | 1 |  |  |  |  |  |  |
| 18 | `referrer_name` | Referrer Name | Data |  |  |  | 1 | 1 |  |  | referrer.employee_name |  |  |  |  |
| 19 | *column_break_14* | **** | _Column Break_ | | | | | | | | | | | | |
| 20 | `is_applicable_for_referral_bonus` | Is Applicable for Referral Bonus | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 21 | `referral_payment_status` | Referral Bonus Payment Status | Select | <br>Unpaid<br>Paid |  |  | 1 |  |  |  |  |  |  |  |  |
| 22 | `department` | Department | Link | -> Department |  |  | 1 |  |  |  | employee.department |  |  |  |  |
| 23 | *additional_information_section* | **Additional Information ** | _Section Break_ | | | | | | | | | | | | |
| 24 | `qualification_reason` | Why is this Candidate Qualified for this Position? | Text Editor |  |  |  |  |  |  |  |  |  |  |  |  |
| 25 | `work_references` | Work References | Text Editor |  |  |  |  |  |  |  |  |  |  |  |  |
| 26 | `amended_from` | Amended From | Link | -> Employee Referral |  |  | 1 |  |  |  |  |  |  |  |  |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 44 chars (empty wrapper only)
