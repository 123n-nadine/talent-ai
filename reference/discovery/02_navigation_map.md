# 02 — Navigation map of the Recruitment area

Screenshots: `screenshots/01_workspace_recruitment.png` (workspace, full page), `screenshots/01_workspace_recruitment_snapshot.yml` (accessibility snapshot), `screenshots/02_recruitment_dashboard.png` (Dashboard "Recruitment").

## Workspace `Recruitment` (hrms, module Recruitment, public)

Workspace body (`Workspace.content`):

| Block | Name | Definition | Custom? |
|---|---|---|---|
| Chart | Job Applicant Pipeline | Dashboard Chart, Group By `Job Applicant.job_title`, Percentage | standard hrms |
| Number card | Job Openings | Count of Job Opening where status = Open | standard |
| Number card | Total Applicants (This month) | Count of Job Applicant, creation this month | standard |
| Number card | Job Offers (This Month) | Count of Job Offer, offer_date this month | standard |
| Quick list | Interviews (This Week) | Interview, `scheduled_on` Timespan this week, docstatus != 2 | standard |

The workspace has **no** link cards / shortcuts in v16; navigation is in the **Workspace Sidebar** record `Recruitment` (hrms) and is then rewritten client-side by the ido_design kit (it removes "Dashboard", adds "Offer Term", "Job Applicant Source" and "Interview Feedback", and shows record counts).

### Sidebar as rendered (left panel)

| Section | Label shown | Target | Type | Notes |
|---|---|---|---|---|
| | Home | `/desk/recruitment` | Workspace | |
| | Hiring Pipeline | `/desk/job-applicant/view/kanban` | URL | Opens the **custom "Hiring pipeline" page** (ido_design) instead of the standard Kanban. Stage tabs Open / Replied / Shortlisted / Accepted / Rejected / Hold, "As a list" toggle, "New Job Applicant". Data from `ido_design.ido_desk.hr.hiring_pipeline`. A standard Kanban Board record named "نت" (public, on `status`) also exists for Job Applicant. |
| | Job Opening (5) | `/desk/job-opening` | DocType | |
| | Job Applicant (5) | `/desk/job-applicant` | DocType | |
| | Interview (2) | `/desk/interview` | DocType | List is re-rendered by the kit as a schedule ("Nothing upcoming…", grouped by day, "The day has passed and the result was never recorded"). |
| | Interview Feedback (1) | `/desk/interview-feedback` | DocType | added by kit |
| | Job Offer (3) | `/desk/job-offer` | DocType | |
| | Appointment Letter | `/desk/appointment-letter` | DocType | |
| Planning | **Hiring Request** | `/desk/job-requisition` | DocType **Job Requisition** | Relabelled "Hiring Request" everywhere in the UI (list title, "New Hiring Request", number card "Time to Fill → Hiring Request"). Sidebar record still says "Job Requisition" → a Translation/label override by the client app. 0 records. |
| Planning | Staffing Plan (2) | `/desk/staffing-plan` | DocType | Custom field on Job Requisition calls it "Workforce Plan"; kit panels call it "Workforce plan". |
| Planning | Employee Referral | `/desk/employee-referral` | DocType | |
| Reports | Recruitment Analytics | `/desk/query-report/Recruitment Analytics` | Script Report (ref Staffing Plan) | only report for recruitment DocTypes |
| Setup | Interview Type (1) | `/desk/interview-type` | DocType | 1 record: "First Round - HR Interview" (no designation, no expected skill set) |
| Setup | Job Opening Template | `/desk/job-opening-template` | DocType | 0 records |
| Setup | Appointment Letter Template | `/desk/appointment-letter-template` | DocType | |
| Setup | Job Offer Term Template (1) | `/desk/job-offer-term-template` | DocType | |
| Setup | Offer Term (19) | `/desk/offer-term` | DocType | added by kit |
| Setup | Job Applicant Source (7) | `/desk/job-applicant-source` | DocType | Website Listing, Walk In, Employee Referral, Campaign, Linkedin, Recommendation, Outsource |
| | Job Portal | `/jobs` | URL (public) | public listing of published openings |
| | Settings | `/desk/hr-settings/HR Settings` | DocType (single) | |
| (hidden by kit) | Dashboard | Dashboard `Recruitment` | | still reachable at `/desk/dashboard-view/Recruitment` |

### Dashboard `Recruitment` (standard hrms)

Number cards: Job Openings, Total Applicants (This month), Accepted Job Applicants, Rejected Job Applicants, Job Offers (This Month), Applicant-to-Hire Percentage, Job Offer Acceptance Rate, Time to Fill (Job Requisition).
Charts (all Group By / Count, standard): Job Applicant Pipeline (job_title), Job Applicant Source (source), Job Applicants by Country (country), Job Application Status (status), Job Offer Status (status), Interview Status (status), Job Application Frequency (count over time), Department Wise Openings, Designation Wise Openings.

## HR Setup workspace (hrms) — recruitment-related items

- Key Reports → **Recruitment Analytics** (Report, depends on Staffing Plan).
- Setup → Company, Branch, Department, Designation (masters used by openings).
- Shortcut **"لوحة المعلومات"** → `https://demo.hs1.ido.sa/ido-hr-dashboard` (client-specific HR dashboard page; not opened in this discovery).
- No other recruitment links. There is no "HR" workspace; HR workspaces are Tenure, Leaves, Expenses, Shift & Attendance, Payroll, Performance, Tax & Benefits, Recruitment, HR Setup, plus **Self Service** (hr_ksa_customization, module HR KSA).

## Client-specific UI (ido_design "IDO Desk kit", `/assets/ido_design/dist/js/idk.bundle.*.js`, 295 KB)

Found by reading the loaded bundle (static asset, GET) and the rendered DOM. None of this is a Client Script / Server Script record; it is app code.

| Where | What it adds | Server method (whitelisted, GET-able) |
|---|---|---|
| Workspace home | "Open positions / Applicants in play / Interviews this week / Offers awaiting a reply" figures and attention notes ("published with no description", "past their closing date") | `ido_design.ido_desk.ws_hr.recruitment_summary` |
| Job Opening form | **Readiness** checklist (5 steps: title/designation/department/company, Job description [hard], Closing date [hard], Linked to a workforce plan, Number of vacancies) with "Go to the field" links; **Candidates** board by status with source / interview count / offer; **Workforce plan** figures (Seats in the plan, Taken by openings, Left, Cost per seat, Budget) and warning "This opening does not say how many of those N seats it takes, so nothing is deducted." | `ido_design.ido_desk.hr_gaps.api.panels` (doctype, name) |
| Staffing Plan form | plan lines (seats/taken/left/cost/budget), openings linked to the plan with a `missing` list (e.g. "Job description", "Closing date"), unlinked openings | same `panels` |
| Job Applicant form | **"Where this applicant stands"**: opening, interviews (date, type), job offer with status; notes "No interview booked yet" / "Interviewed, with no offer on file". Also makes `Attach` fields read-only-looking on saved docs (`attach_read`). | `panels` |
| Job Requisition form | custom fields `staffing_plan` (Workforce Plan), `plan_seats_left` (read-only Int) and `plan_over_notice` (HTML "This request asks for more than the plan has left."); values filled by `hr_gaps.api.evaluate` (returns `values` to set on the form, client-side) | `ido_design.ido_desk.hr_gaps.api.evaluate` (doctype, doc) |
| List views | extra row info (e.g. interview list as schedule) | `ido_design.ido_desk.hr_gaps.api.list_extras` (doctype, names) |
| Job Applicant Kanban route | replaced by the **Hiring pipeline** page (stages Open→Replied→Shortlisted→Accepted; outcomes Rejected/Hold; card shows designation, "Not rated yet", interview count) | `ido_design.ido_desk.hr.hiring_pipeline` |
| Sidebar | removes Dashboard; adds Offer Term, Job Applicant Source, Interview Feedback; counts per item | `ido_design.ido_desk.api.counts` |
| Other HR | `hr.requests_inbox`, `hr.decide_request`, `hr.roster`, `hr.self_service`, `leave_cal.leave_calendar`, `hr.payroll_summary`, `hr.expenses_summary`, `hr.hr_setup_summary`, `ws_hr.*_summary`, `api.home_summary`, `api.set_language` | not recruitment |

The Job Opening readiness rule set returned by `panels` (evidence for the gap analysis):

| Step | hard | Message when not ok | Field |
|---|---|---|---|
| Title, designation, department and company | | "One of them is empty, so the opening cannot be placed in a department's plan." | |
| Job description | yes | "Published on the careers site with no description — an applicant opens an empty page." | description |
| Closing date | yes | "Closed on <date> and the opening is still Open." | closes_on |
| Linked to a workforce plan | | "Not linked to a plan, so this vacancy is not counted against any budget." | staffing_plan |
| Number of vacancies | | "Vacancies is zero on this opening, though its plan allows N." | vacancies |

`hiring_pipeline` returns, per applicant: name, applicant_name, status, opening, designation, rating, interviews, offer, modified. `panels` for Job Opening returns: ready[], applicants[] (name, applicant_name, status, source, interviews, offer), stages, outcomes, plan {seats, taken, left, cost, budget, openings}, plan_candidates, currency.

Note: the kit also contains a panel "How the final score was reached … Final score / 5 … the mean of the three" — this belongs to the **Appraisal** (KRA/KPI/KBI) feature of the HR KSA app, not to recruitment. There is no AI/CV scoring anywhere in the kit (keywords `resume`, `cv`, `rank`, `ocr`, `llm`, `openai` have no recruitment hits).

## Desk views and actions observed (names only, nothing clicked that changes data)

| View | Columns | Standard filters (quick filter bar) | Primary / form buttons | Connections |
|---|---|---|---|---|
| Job Applicant list (`10_job_applicant_list.png`) | Full Name (subject), ID, Status, Designation, Job Opening, Applicant Rating | ID, Full Name shown in bar; meta flags `in_standard_filter` on job_title, status, applicant_rating | New Job Applicant; Kanban View / Report View / Dashboard View; Saved filters (none), List Settings, Customize | — |
| Job Applicant form (`11_job_applicant_form_details.png`) | tabs Details / Salary Expectation; sections Details, Resume, Source | | **Create Employee**, **View Job Offer** (custom_buttons), menu: Email, Rename, Duplicate, Delete… | Employee, Employee Onboarding, Job Offer, Appointment Letter, Interview (form dashboard links with "+"); kit panel "Where this applicant stands" |
| Hiring pipeline (`12_…_hiring_pipeline.png`) | stage tabs with counts | stage=Open query param | As a list, New Job Applicant | |
| Job Opening list (`20_job_opening_list.png`) | Job Title, ID, Status, Closes On, Vacancies, Department | name, job_title, designation, status, company, department, employment_type, publish | New Job Opening | |
| Job Opening form (`21_job_opening_form.png`) | tabs Details / Pay Details; sections Details, Company Details, References (collapsible: Staffing Plan, Planned Positions, Job Requisition, Vacancies), publish section, Description | | **Close Job Opening** (custom button); Save | Job Applicant (+); kit panels Readiness / Candidates / Workforce plan |
| Staffing Plan list (`30_staffing_plan_list.png`) | ID, Status (Submitted), From Date, Department | name | New Staffing Plan | |
| Staffing Plan form (`31_staffing_plan_form.png`, submitted record) | Company, Department, From/To Date, **Get Job Requisitions** button, Staffing Details grid (Designation, Vacancies, Estimated Cost Per Position, Total Estimated Cost, Number Of Positions), Total Estimated Budget | | Cancel (submitted doc), Duplicate | Job Opening (1) |
| Hiring Request = Job Requisition list (`40_job_requisition_list.png`) | Designation (subject), ID, Status, Posting Date, Department, No of Positions | name, designation, requested_by | New Hiring Request | empty: "You haven't created a Hiring Request yet" |
| Interview list (`60_interview_list.png`) | Job Applicant (subject), ID, Status, Scheduled On, Designation, Interview Type | name, interview_type, job_applicant, designation, status, scheduled_on | New Interview | rendered as schedule by kit |
| Job Offer list (`61_job_offer_list.png`) | Applicant Name (subject), ID, Status, Designation | name, applicant_name, status | New Job Offer | |

Saved list filters (`List Filter`): none for any recruitment DocType. `List View Settings`: none (404 for the 4 main DocTypes). User-level list settings for Job Applicant: empty. So the "many list filters" the HR team uses are ad-hoc filters, not saved ones — at least on this demo.
