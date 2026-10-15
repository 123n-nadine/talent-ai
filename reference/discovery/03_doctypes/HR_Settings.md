# HR Settings

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `-` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | *employee_tab* | **Employee** | _Tab Break_ | | | | | | | | | | | | |
| 2 | *employee_settings_section* | **Employee Settings** | _Section Break_ | | | | | | | | | | | | |
| 3 | `emp_created_by` | Employee Naming By | Select | Naming Series<br>Employee Number<br>Full Name |  |  |  |  |  |  |  | Naming Series |  |  | Employee records are created using the selected option |
| 4 | `standard_working_hours` | Standard Working Hours | Float |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 | *column_break_lrow* | **** | _Column Break_ | | | | | | | | | | | | |
| 6 | `retirement_age` | Retirement Age (In Years) | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 7 | *reminders_section* | **Reminders** | _Section Break_ | | | | | | | | | | | | |
| 8 | *column_break_11* | **** | _Column Break_ | | | | | | | | | | | | |
| 9 | `send_work_anniversary_reminders` | Work Anniversaries  | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 10 | `send_birthday_reminders` | Birthdays | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 11 | `send_holiday_reminders` | Holidays | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 12 | `frequency` | Set the frequency for holiday reminders | Select | Weekly<br>Monthly |  |  |  |  |  | eval:doc.send_holiday_reminders |  | Weekly |  |  |  |
| 13 | *column_break_hyec* | **** | _Column Break_ | | | | | | | | | | | | |
| 14 | `sender` | Sender | Link | -> Email Account |  |  |  |  |  |  |  |  |  |  |  |
| 15 | `sender_email` | Sender Email | Data |  |  |  | 1 |  |  | eval:doc.sender | sender.email_id |  |  |  |  |
| 16 | *leaves_tab* | **Leaves** | _Tab Break_ | | | | | | | | | | | | |
| 17 | *leave_settings_section* | **Leave Settings** | _Section Break_ | | | | | | | | | | | | |
| 18 | `auto_leave_encashment` | Auto Leave Encashment | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 19 | `leave_approver_mandatory_in_leave_application` | Leave Approver Mandatory In Leave Application | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 20 | `prevent_self_leave_approval` | Prevent self approval for leaves even if user has permissions | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 21 | `show_leaves_of_all_department_members_in_calendar` | Show Leaves Of All Department Members In Calendar | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 22 | *column_break_29* | **** | _Column Break_ | | | | | | | | | | | | |
| 23 | `send_leave_notification` | Send Leave Notification | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 24 | `leave_approval_notification_template` | Leave Approval Notification Template | Link | -> Email Template |  |  |  |  |  | eval: doc.send_leave_notification == 1 |  |  |  |  |  |
| 25 | `leave_status_notification_template` | Leave Status Notification Template | Link | -> Email Template |  |  |  |  |  | eval: doc.send_leave_notification == 1 |  |  |  |  |  |
| 26 | `restrict_backdated_leave_application` | Restrict Backdated Leave Application | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 27 | `role_allowed_to_create_backdated_leave_application` | Role Allowed to Create Backdated Leave Application | Link | -> Role |  |  |  |  |  | eval:doc.restrict_backdated_leave_application == 1 |  |  |  |  |  |
| 28 | *expenses_tab* | **Expenses** | _Tab Break_ | | | | | | | | | | | | |
| 29 | *expenses_settings_section* | **Expenses Settings** | _Section Break_ | | | | | | | | | | | | |
| 30 | `expense_approver_mandatory_in_expense_claim` | Expense Approver Mandatory In Expense Claim | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 31 | `prevent_self_expense_approval` | Prevent self approval for expense claims even if user has permissions | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 32 | `unlink_payment_on_cancellation_of_employee_advance` |  Unlink Payment on Cancellation of Employee Advance | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 33 | *ksa_excuse_policy_section* | **Excuse Policy (KSA)** | _Section Break_ | | | | | | | | | | | | |
| 34 | `excuse_type` | Excuse Type | Select | <br>Personal<br>Official |  |  |  |  |  |  |  |  | YES |  |  |
| 35 | `max_excuse_days` | Maximum Excuse Days Per Month | Int |  |  |  |  |  |  |  |  |  | YES |  |  |
| 36 | `max_excuse_hours` | Maximum Excuse Hours Per Month | Time |  |  |  |  |  |  |  |  |  | YES |  |  |
| 37 | *ksa_missing_punch_section* | **Missing Punch Policy (KSA)** | _Section Break_ | | | | | | | | | | | | |
| 38 | `max_missing_punch_days` | Maximum Missing Punch Days Per Month | Int |  |  |  |  |  |  |  |  |  | YES |  |  |
| 39 | `enable_multi_currency_expense_claim` | Enable Multi-Currency Expense Claims | Check |  |  |  |  |  |  |  |  | 0 |  |  | Allow expense claims to be raised in a currency other than the company currency |
| 40 | *shift_and_attendance_tab* | **Shift and Attendance** | _Tab Break_ | | | | | | | | | | | | |
| 41 | *shift_settings_section* | **Shift Settings** | _Section Break_ | | | | | | | | | | | | |
| 42 | `allow_multiple_shift_assignments` | Allow Multiple Shift Assignments for Same Date | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 43 | *attendance_settings_section* | **Attendance Settings** | _Section Break_ | | | | | | | | | | | | |
| 44 | `allow_employee_checkin_from_mobile_app` | Allow Employee Checkin from Mobile App | Check |  |  |  |  |  |  |  |  | 1 |  |  |  |
| 45 | `allow_geolocation_tracking` | Allow Geolocation Tracking | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 46 | *tenure_tab* | **Tenure** | _Tab Break_ | | | | | | | | | | | | |
| 47 | *employee_exit_settings_section* | **Employee Exit Settings** | _Section Break_ | | | | | | | | | | | | |
| 48 | `exit_questionnaire_web_form` | Exit Questionnaire Web Form | Link | -> Web Form |  |  |  |  |  |  |  |  |  |  |  |
| 49 | `exit_questionnaire_notification_template` | Exit Questionnaire Notification Template | Link | -> Email Template |  |  |  |  |  |  |  |  |  |  |  |
| 50 | *recruitment_tab* | **Recruitment** | _Tab Break_ | | | | | | | | | | | | |
| 51 | *hiring_settings_section* | **Hiring Settings** | _Section Break_ | | | | | | | | | | | | |
| 52 | `check_vacancies` | Check Vacancies On Job Offer Creation | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 53 | `send_interview_reminder` | Send Interview Reminder | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 54 | `interview_reminder_template` | Interview Reminder Notification Template | Link | -> Email Template |  |  |  |  |  | send_interview_reminder |  |  |  |  |  |
| 55 | `remind_before` | Remind Before | Time |  |  |  |  |  |  | send_interview_reminder |  | 00:15:00 |  |  |  |
| 56 | `send_interview_feedback_reminder` | Send Interview Feedback Reminder | Check |  |  |  |  |  |  |  |  | 0 |  |  |  |
| 57 | `feedback_reminder_notification_template` | Feedback Reminder Notification Template | Link | -> Email Template |  |  |  |  |  | send_interview_feedback_reminder |  |  |  |  |  |
| 58 | *column_break_4* | **** | _Column Break_ | | | | | | | | | | | | |
| 59 | `hiring_sender` | Sender | Link | -> Email Account |  |  |  |  |  |  |  |  |  |  |  |
| 60 | `hiring_sender_email` | Sender Email | Data |  |  |  | 1 |  |  | eval:doc.hiring_sender | hiring_sender.email_id |  |  |  |  |

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 38 chars (empty wrapper only)
