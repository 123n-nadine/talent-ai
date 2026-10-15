# 01 — Environment fingerprint

Site: `https://demo.hs1.ido.sa` (site name `demo.hs1.ido.sa`). Discovery date: 2026-10-12. All data read with GET only.

## Session used

- Logged in as a shared demo System User (System Manager, HR Manager, HR User, Interviewer and ~115 other roles). The account has no API key/secret set (`User.api_key` empty), so REST access in this discovery relied on the browser session cookie.
- Desk language of this user: **en**. Site default language: **ar**. Both `ar` and `en` Language records are enabled.
- Time zone: **Africa/Cairo** (not Asia/Riyadh). Country: Saudi Arabia. Currency: SAR. Date format `dd-mm-yyyy`, week starts Sunday, float precision 3.

## Versions (`frappe.utils.change_log.get_versions`)

| App | Title | Branch | Version | Notes |
|---|---|---|---|---|
| frappe | Frappe Framework | version-16 | **16.31.0** | `/desk/` URL prefix, Workspace Sidebar DocType |
| erpnext | ERPNext | version-16 | **16.32.0** | |
| hrms | Frappe HR | **develop** | **17.0.0-dev** | recruitment module comes from here; running a develop branch on a demo |
| hr_ksa_customization | Hr_KSA_Customization | End_Service | 0.0.1 | custom app, module **HR KSA** (KSA payroll/allowances, termination, exit re-entry, excuse requests, onboarding documents, KPI/KBI appraisal). No recruitment DocTypes. |
| ido_design | I Do Design | new-design | 0.0.1 | custom app, modules **I Do Design** and **IDO Desk**. Theme + "IDO Desk kit" (`idk.bundle.js`) that injects recruitment panels, the Hiring pipeline page, sidebar edits, and the 3 custom fields / 5 property setters found on Job Requisition and Job Opening (module = IDO Desk, created 2026-10-04). |
| ido_api | Ido Api | master | 0.0.1 | API layer for the mobile app |
| ido_chat | IDO Chat | master | 1.3.913 | business chat (floating chat widget also appears on public pages) |
| ido_event | IDO Event | main | 0.0.1 | event management (contains "IDO Security Vetting", which is event-visitor vetting, not recruitment) |
| ido_camera, ido_lost_and_found, push_notification | | | 0.0.1 | mobile-app related |
| real_estate, cleaning_app, maintenanceapp, agriculture, work_permit, issue | | | 0.0.1 | other client verticals sharing the demo |
| lending | Lending | develop | 17.0.0-dev | |

Module Def also lists apps `ido_core` (module "Ido Core") and `laf_module` ("Lost and Found") that are not in `get_versions` (installed apps list vs. module registry mismatch, harmless).

## System Settings relevant to recruitment / integration

| Setting | Value | Impact |
|---|---|---|
| `enable_scheduler` | **0** | Background scheduler is disabled on this site. Last `Scheduled Job Log` entry: 2025-08-21. `close_expired_job_openings`, interview reminders, feedback reminders will not run. 3 of 5 openings are past their closing date and still Open. |
| `allow_guests_to_upload_files` | 0 | Guests can still upload through the public web form because Web Form uploads go through the web form's own permission path, but any extra guest upload endpoint is blocked. Confirm with the Frappe team (open question). |
| `max_file_size` | 0 (site default) | Web form `max_attachment_size` is also 0 → framework default applies. |
| `apply_strict_user_permissions` | 0 | |
| `disable_signup` (Website Settings) | 1 | Applicants cannot create portal accounts; application is anonymous (Guest). |

## HR Settings (recruitment part)

| Field | Value |
|---|---|
| `check_vacancies` (Check Vacancies On Job Offer Creation) | 0 |
| `send_interview_reminder` | 0 (remind_before 00:15:00) |
| `send_interview_feedback_reminder` | 0 |
| `emp_created_by` | Employee Number |
| Custom (HR KSA) fields on HR Settings | `excuse_type`, `max_excuse_days`, `max_excuse_hours`, `max_missing_punch_days` (not recruitment) |

## Language / RTL

- Desk renders LTR English for this user (`html dir=ltr`, `lang=en`). Switching the user language to `ar` would render the desk RTL (standard Frappe behaviour, not tested to avoid changing user data).
- Public pages (`/jobs`, job page, `/job_application/new`) render in English by default for this session; appending `?_lang=ar` renders the application form fully in Arabic with `dir=rtl` (labels: الاسم الكامل, البريد الإلكتروني, رقم الهاتف, بلد الإقامة, المصدر, خطاب التقديم, رابط السيرة الذاتية, مرفق السيرة الذاتية, العملة, النطاق الأدنى, النطاق الأعلى; buttons إرفاق / تجاهل / تسجيل). Screenshot: `screenshots/53_public_job_application_webform_arabic.png`.
- The custom IDO Desk kit (ido_design) has an API `ido_design.ido_desk.api.set_language`, i.e. a language switcher in the desk header (globe icon).

## Evidence

- `_log.md` rows for step 1; raw values in `_raw_integration.json` (boot flags) and the session check result.
