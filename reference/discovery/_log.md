# API / navigation log

All requests were HTTP GET issued from `browser_evaluate` with `fetch()` or plain browser navigation. No POST/PUT/DELETE, no `frappe.call`, no form submission, no file upload. Response bodies are not recorded here. Filters and fields are shown URL-decoded for readability.

| step | request | status | note |
|---|---|---|---|
| 0 | `/api/method/frappe.auth.get_logged_user` | 200 | session check |
| 1 | `/api/method/frappe.utils.change_log.get_versions` | 200 | app versions |
| 1 | `/api/resource/System Settings/System Settings` | 200 | language/timezone |
| 1 | `/api/resource/Language?fields=[name,language_name,enabled]&filters=[name in ar,en]` | 200 |  |
| 2 | `/api/resource/Workspace?fields=[...]&limit_page_length=300` | 200 | workspace list |
| 2 | `/api/resource/Workspace/Recruitment` | 200 |  |
| 2 | `/api/resource/Workspace/HR` | 404 | no such workspace |
| 2 | `/api/resource/Workspace/Human Resources` | 404 | no such workspace |
| 2 | `/api/resource/Workspace/HR Setup` | 200 |  |
| 2 | `/api/resource/Workspace/Recruitment` | 200 | content JSON |
| 2 | `/api/resource/Workspace Sidebar/Recruitment` | 200 | v16 sidebar items |
| 2 | `/api/resource/Number Card/Job Openings` | 200 |  |
| 2 | `/api/resource/Number Card/Total Applicants (This month)` | 200 |  |
| 2 | `/api/resource/Number Card/Job Offers (This Month)` | 200 |  |
| 2 | `/api/resource/Dashboard Chart/Job Applicant Pipeline` | 200 |  |
| 2 | `/api/resource/HR Settings/HR Settings` | 200 |  |
| 2 | `/api/resource/Dashboard/Recruitment` | 200 |  |
| 2 | `/api/resource/Report?filters=[ref_doctype in recruitment DocTypes]` | 200 |  |
| 2 | `/api/resource/Number Card?filters=[document_type in recruitment DocTypes]` | 200 |  |
| 2 | `/api/resource/Dashboard Chart?filters=[document_type in recruitment DocTypes]` | 200 |  |
| 2 | `/api/resource/Kanban Board?filters=[reference_doctype in ...]` | 200 |  |
| 3 | `/api/resource/DocType?filters=[module in ...]&fields=[name,custom,istable,issingle,module,app] (+21 name-like variants)` | 417 | ValidationError: field 'app' does not exist on DocType; retried without it |
| 7 | `/api/method/ido_design.ido_desk.hr_gaps.api.panels?doctype=Job Opening&name=HR-OPN-2026-0006` | 200 | custom app read API |
| 7 | `/api/method/ido_design.ido_desk.hr_gaps.api.panels?doctype=Staffing Plan&name=hr` | 200 | custom app read API |
| 7 | `/api/method/ido_design.ido_desk.hr.hiring_pipeline` | 200 | custom app read API |
| 7 | `/api/method/ido_design.ido_desk.ws_hr.recruitment_summary` | 200 | custom app read API |
| 5 | `/api/resource/Job Applicant?filters=[job_title != '']&fields=[name]&limit_page_length=1 (x3)` | 200 | to route to a form without typing an ID |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=<6 recruitment DocTypes> (second pass, JS grep)` | 200 |  |
| 5 | `/assets/ido_design/dist/js/idk.bundle.*.js (static asset, fetched twice for grep)` | 200 |  |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Staffing Plan` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Requisition` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Opening` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Applicant` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Interview` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Offer` | 200 | from _raw_core_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Opening Template` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Applicant Source` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Interview Type` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Interview Round` | 404 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Interview Feedback` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Appointment Letter` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Appointment Letter Template` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Employee Referral` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Designation` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Skill` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Department` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Employment Type` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Branch` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Offer Term` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Offer Term Template` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/method/frappe.desk.form.load.getdoctype?doctype=HR Settings` | 200 | from _raw_secondary_doctypes.json |
| 3 | `/api/resource/Custom Field?filters=[["dt","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","dt","fieldname","label","fieldtype","options","reqd","hidden","read_only","insert_after","module","owner","creation","in_list_view","in_standard_filter","depends_on","fetch_from","description"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Property Setter?filters=[["doc_type","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","doc_type","field_name","property","value","property_type","doctype_or_field","module","creation"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Workflow?filters=[["document_type","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","document_type","is_active","workflow_state_field"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Workflow?fields=["name","document_type","is_active"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Client Script?filters=[["dt","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","dt","view","enabled","module","script"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Server Script?filters=[["reference_doctype","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","script_type","reference_doctype","doctype_event","api_method","disabled","module","script"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Server Script?fields=["name","script_type","reference_doctype","api_method","disabled"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Notification?filters=[["document_type","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","document_type","event","enabled","channel","condition","subject","send_to_all_assignees","module","is_standard"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Assignment Rule?filters=[["document_type","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","document_type","disabled","assign_condition","unassign_condition","rule","priority"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Webhook?fields=["name","webhook_doctype","webhook_docevent","enabled","request_url","request_method"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/Print Format?filters=[["doc_type","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","doc_type","standard","disabled","custom_format","print_format_type"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/List View Settings?filters=[["name","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["name","fields","disable_count","disable_sidebar_stats","disable_auto_refresh","total_fields"]&limit_page_length=200` | 417 | from _raw_customizations.json |
| 3 | `/api/resource/Email Template?filters=[["name","like","%interview%"]]&fields=["name","subject"]&limit_page_length=200` | 200 | from _raw_customizations.json |
| 3 | `/api/resource/DocType Link?filters=[["parent","in",["Staffing Plan","Staffing Plan Detail","Job Requisition","Job Opening","Job Opening Template","Job Applicant","Job Applicant Source","Interview","Interview Type","Interview Feedback","Interview Detail","Job Offer","Job Offer Term","Appointment Letter","Employee Referral","Designation","Designation Skill","Skill","Employment Type","Interviewer","Expected Skill Set","Skill Assessment"]]]&fields=["parent","link_doctype","link_fieldname","group","custom","table_fieldname","parent_doctype"]&limit_page_length=200` | 403 | from _raw_customizations.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Staffing Plan` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Staffing Plan?fields=["name","company","department","from_date","to_date","total_estimated_budget","docstatus","creation"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Job Requisition` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Job Requisition?fields=["name","designation","staffing_plan","plan_seats_left","department","no_of_positions","expected_compensation","company","status","requested_by","requested_by_dept","requested_by_designation","posting_date","completed_on","expected_by","time_to_fill","description","reason_for_requesting","creation"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Job Opening` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Job Opening?fields=["name","job_opening_template","job_title","designation","status","posted_on","closes_on","closed_on","company","department","employment_type","location","staffing_plan","planned_vacancies","job_requisition","vacancies","publish","prevent_duplicate_applicant","route","publish_applications_received","job_application_route","description","currency","lower_range","upper_range","salary_per","publish_salary_range","creation"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Job Applicant` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Job Applicant?fields=["name","applicant_name","email_id","phone_number","job_title","designation","country","status","applicant_rating","resume_link","cover_letter","resume_attachment","notes","source","source_name","employee_referral","currency","lower_range","upper_range","creation","owner"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Interview` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Interview?fields=["name","interview_type","job_applicant","job_opening","designation","resume_link","status","scheduled_on","from_time","to_time","expected_average_rating","average_rating","interview_summary","docstatus","creation"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4 | `/api/method/frappe.client.get_count?doctype=Job Offer` | 200 | from _raw_data_profile.json |
| 4 | `/api/resource/Job Offer?fields=["name","job_applicant","applicant_name","applicant_email","offer_date","designation","company","status","job_offer_term_template","select_terms","terms","letter_head","docstatus","creation"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_data_profile.json |
| 4/6 | `/api/method/frappe.client.get_count?doctype=File&filters=[["attached_to_doctype","in",["Job Applicant","Job Opening","Job Requisition","Interview","Job Offer","Employee Referral"]]]` | 200 | from _raw_webform_attachments.json |
| 4/6 | `/api/resource/File?filters=[["attached_to_doctype","in",["Job Applicant","Job Opening","Job Requisition","Interview","Job Offer","Employee Referral"]]]&fields=["file_name","file_size","is_private","attached_to_field","attached_to_doctype","creation","owner"]&order_by=creation desc&limit_page_length=200` | 200 | from _raw_webform_attachments.json |
| 4/6 | `/api/resource/Job Opening?filters=[["publish","=",1]]&fields=["name","job_title","status","route","job_application_route","designation","closes_on"]&limit_page_length=20` | 200 | from _raw_webform_attachments.json |
| 4/6 | `/api/resource/Web Form?fields=["name","title","doc_type","route","published","login_required","allow_multiple","allow_edit","allow_delete","allow_incomplete","allow_print","anonymous","apply_document_permissions","is_standard","module","max_attachment_size","allow_comments","show_attachments","condition_json","success_url","client_script"]&limit_page_length=200` | 200 | from _raw_webform_attachments.json |
| 4/6 | `/api/resource/Web Form/job-application` | 200 | from _raw_webform_attachments.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%llm%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%openai%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%gpt%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%gemini%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%claude%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%anthropic%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%parse%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%whisper%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%vision%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%ocr%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%ai %"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%ai_%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/DocType?filters=[["name","like","%AI%"]]&fields=["name","module","custom","istable"]&limit_page_length=50` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Module Def?fields=["name","app_name","custom"]&limit_page_length=300` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Scheduled Job Type?fields=["name","method","frequency","stopped","cron_format","last_execution"]&filters=[["method","like","%hrms%"]]&limit_page_length=200` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Scheduled Job Type?fields=["name","method","frequency","stopped","last_execution"]&filters=[["method","like","%hr_ksa%"]]&limit_page_length=200` | 200 | from _raw_integration.json |
| 7 | `/api/method/frappe.client.get_count?doctype=Scheduled Job Type` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Scheduled Job Log?fields=["name","creation"]&order_by=creation desc&limit_page_length=1` | 200 | from _raw_integration.json |
| 7 | `/api/resource/User/<logged-in user>` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Custom Field?fields=["dt","count(name) as n"]&filters=[["dt","in",["Employee","Job Applicant","Job Opening","Job Requisition","Staffing Plan","Interview","Job Offer","Designation","Department","Appointment Letter","Employee Referral"]]]&group_by=dt&limit_page_length=50` | 417 | from _raw_integration.json |
| 7 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Employee` | 200 | from _raw_integration.json |
| 7 | `/api/method/frappe.model.utils.user_settings.get?doctype=Job Applicant` | 200 | from _raw_integration.json |
| 7 | `/api/resource/List Filter?fields=["name","filter_name","reference_doctype","for_user","filters"]&filters=[["reference_doctype","in",["Job Applicant","Job Opening","Job Requisition","Staffing Plan","Interview","Job Offer"]]]&limit_page_length=100` | 200 | from _raw_integration.json |
| 7 | `/api/resource/Report View Settings?limit_page_length=1` | 404 | from _raw_integration.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Requisition` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Opening` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Applicant` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Staffing Plan` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Interview` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.desk.form.load.getdoctype?doctype=Job Offer` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/List View Settings/Job Applicant` | 404 | from _raw_ui_prep.json |
| 5 | `/api/resource/List View Settings/Job Opening` | 404 | from _raw_ui_prep.json |
| 5 | `/api/resource/List View Settings/Job Requisition` | 404 | from _raw_ui_prep.json |
| 5 | `/api/resource/List View Settings/Staffing Plan` | 404 | from _raw_ui_prep.json |
| 5 | `/api/resource/Kanban Board?fields=["name","reference_doctype","field_name","columns","private","filters"]&filters=[["reference_doctype","=","Job Applicant"]]` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Job Opening?fields=["name","status","publish","staffing_plan","job_requisition","designation","department"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Staffing Plan?fields=["name","department","docstatus"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Staffing Plan Detail?fields=["parent","designation","vacancies","number_of_positions","current_count","current_openings","estimated_cost_per_position"]&limit_page_length=50&parent=Staffing Plan` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Job Applicant?fields=["name","status","job_title","designation","country","source","creation"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Interview?fields=["name","status","job_opening","designation","docstatus","interview_type"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Job Offer?fields=["name","status","designation","docstatus","job_offer_term_template"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Job Opening Template?fields=["name","designation","department"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Interview Type?fields=["name","designation","expected_average_rating"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Job Applicant Source?fields=["name"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.client.get_count?doctype=Designation` | 200 | from _raw_ui_prep.json |
| 5 | `/api/method/frappe.client.get_count?doctype=Designation Skill` | 403 | from _raw_ui_prep.json |
| 5 | `/api/resource/Skill?fields=["name"]&limit_page_length=50` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Designation?fields=["name","description"]&limit_page_length=200` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Employment Type?fields=["name"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Branch?fields=["name"]&limit_page_length=30` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Company?fields=["name","country","default_currency"]&limit_page_length=20` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Portal Settings/Portal Settings` | 200 | from _raw_ui_prep.json |
| 5 | `/api/resource/Website Settings/Website Settings` | 200 | from _raw_ui_prep.json |
| 7 | `/assets/ido_design/dist/js/ido_design.bundle.U3W5SFKU.js` | 200 | from _raw_app_js_grep.json |
| 7 | `/api/method/ido_design.api.theme_js` | 200 | from _raw_app_js_grep.json |
| 7 | `/assets/ido_design/dist/js/idk.bundle.DQOBYY2K.js` | 200 | from _raw_app_js_grep.json |
| 7 | `/assets/ido_design/dist/js/ido_org_chart_boot.bundle.OJJRE2WI.js` | 200 | from _raw_app_js_grep.json |
| 7 | `/assets/ido_event/js/ido_engine_client.js` | 200 | from _raw_app_js_grep.json |
| 7 | `/assets/ido_event/js/ido_workspace_event.js` | 200 | from _raw_app_js_grep.json |
| 0 | `GET https://demo.hs1.ido.sa/desk/recruitment (browser navigation)` | 302->login then 200 after user login |  |
| 5 | `GET /desk/job-applicant, /desk/job-opening, /desk/job-opening/HR-OPN-2026-0006, /desk/staffing-plan, /desk/staffing-plan/hr, /desk/job-requisition, /desk/job-applicant/view/kanban, /desk/dashboard-view/Recruitment, /desk/interview/view/list, /desk/job-offer/view/list (desk routes)` | 200 |  |
| 6 | `GET /jobs (public portal)` | 200 |  |
| 6 | `GET /jobs/contracting_eg/customer-service-representative` | net::ERR_CONNECTION_CLOSED on first try, 200 on retry | transient |
| 6 | `GET /job_application/new?job_title=HR-OPN-2026-0006` | 200 | web form, not submitted |
| 6 | `GET /job_application/new?job_title=HR-OPN-2026-0006&_lang=ar` | 200 | Arabic/RTL check |

## Status summary (API calls)

- 200: 128
- 403: 2
- 404: 8
- 417: 3

Notes:
- 417 = Frappe ValidationError (bad field name in `fields`), 403 = PermissionError (`DocType Link` list, `Designation Skill` get_count), 404 = record does not exist (`List View Settings` for the 4 DocTypes, `Report View Settings`, `Workspace/HR`).
