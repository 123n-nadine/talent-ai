# Job Offer

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 1 · naming: `HR-OFF-.YYYY.-.#####` · title field: `applicant_name`

Record count: see 07_data_profile.md. Fill rates below come from the 3 record(s) sampled.

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `job_applicant` | Job Applicant | Link | -> Job Applicant |  |  |  |  |  | eval:doc.job_applicant |  |  |  | 100 |  |
| 2 | `applicant_name` | Applicant Name | Data |  | 1 |  |  | 1 |  |  | job_applicant.applicant_name |  |  | 100 |  |
| 3 | `applicant_email` | Applicant Email Address | Data | Email | 1 |  |  |  |  |  | job_applicant.email_id |  |  | 100 |  |
| 4 | *column_break_3* | **** | _Column Break_ | | | | | | | | | | | | |
| 5 | `offer_date` | Offer Date | Date |  | 1 |  |  |  |  |  |  |  |  | 100 |  |
| 6 | `designation` | Designation | Link | -> Designation | 1 |  |  | 1 |  |  | job_applicant.designation |  |  | 100 |  |
| 7 | `company` | Company | Link | -> Company | 1 |  |  | 1 |  |  |  |  |  | 100 |  |
| 8 | `status` | Status | Select | Awaiting Response<br>Accepted<br>Rejected<br>Cancelled |  |  |  |  | 1 |  |  |  |  | 100 |  |
| 9 | *section_break_4* | **** | _Section Break_ | | | | | | | | | | | | |
| 10 | `job_offer_term_template` | Job Offer Term Template | Link | -> Job Offer Term Template |  |  |  |  |  |  |  |  |  | 33 |  |
| 11 | `offer_terms` | Job Offer Terms | Table | child -> **Job Offer Term** |  |  |  |  |  |  |  |  |  |  |  |
| 12 | *section_break_14* | **** | _Section Break_ | | | | | | | | | | | | |
| 13 | `select_terms` | Select Terms and Conditions | Link | -> Terms and Conditions |  |  |  |  |  |  |  |  |  | 0 |  |
| 14 | `terms` | Terms and Conditions | Text Editor |  |  |  |  |  |  |  |  |  |  | 0 |  |
| 15 | *printing_details* | **Printing Details** | _Section Break_ | | | | | | | | | | | | |
| 16 | `letter_head` | Letter Head | Link | -> Letter Head |  |  |  |  |  |  | company.default_letter_head |  |  | 0 |  |
| 17 | *column_break_16* | **** | _Column Break_ | | | | | | | | | | | | |
| 18 | `select_print_heading` | Print Heading | Link | -> Print Heading |  |  |  |  |  |  |  |  |  |  |  |
| 19 | `amended_from` | Amended From | Link | -> Job Offer |  |  | 1 |  |  |  |  |  |  |  |  |

## Child tables

- `offer_terms` (Table) -> **Job Offer Term** — see `Job_Offer_Term.md`

## Role permissions

| role | read | write | create | submit | cancel | delete | if_owner | permlevel |
|---|---|---|---|---|---|---|---|---|
| HR User | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Support Read Only | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 36 chars (empty wrapper only)
