# Guide coverage — every item of the system, its page, a screenshot and its test

Built from the code and the docs by `tools/guide/inventory.py` (not from memory) and written by `tools/guide/build.py` from the same build as
`talent-ai-full-guide.pdf`: the page is where the item's code (e.g. `EP-012`) is printed in the PDF, the screenshot is the picture of that
page (or, for items without a natural picture such as endpoints and settings, the API docs, the settings screen or a rendering of the
settings file without values), and the test is a section of `docs/TEST_REPORT.md`. `tools/guide/coverage_check.py` re-reads the code and
checks that nothing is missing.

**581 items**, 581 with all three columns filled.

| Category | Items |
|---|---|
| screen | 31 |
| doctype | 11 |
| button | 84 |
| field | 37 |
| endpoint | 67 |
| hook | 10 |
| stage | 10 |
| flag | 13 |
| status | 33 |
| setting | 77 |
| role | 16 |
| command | 73 |
| decision | 71 |
| evaluation | 10 |
| security | 19 |
| architecture | 19 |

| Code | Category | Item | Guide page (PDF) | Screenshot | Test (TEST_REPORT.md) |
|---|---|---|---|---|---|
| SC-001 | screen | `Frappe page /desk/ai-batch` | 41 | [S07_batch.png](images/fit/S07_batch.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-002 | screen | `Frappe page /desk/ai-ranking` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-003 | screen | `Frappe page /desk/ai-recruitment` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-004 | screen | `Frappe page /desk/ai-talent-pool` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-005 | screen | `Frappe page /desk/talent-ai` | 25 | [S00_cycle_map_1.png](images/steps/S00_cycle_map_1.png) | §2 roles matrix (every role opened it), §7 P01 |
| DT-001 | doctype | `AI Applicant Answer` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe test suite, §2 roles matrix |
| DT-002 | doctype | `AI Assessment Evidence` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §10 Frappe test suite, §2 roles matrix |
| DT-003 | doctype | `AI Candidate Assessment` | 43 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_edit_after_evaluation_makes_the_result_stale` |
| SC-006 | screen | `Frappe list and form /desk/ai-candidate-assessment` | 43 | [S09_head.png](images/steps/S09_head.png) | §2 roles matrix (every role opened it), §7 P01 |
| DT-004 | doctype | `AI Job Criterion` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe test suite, §2 roles matrix |
| DT-005 | doctype | `AI Job Profile` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe `test_weights_must_total_100_to_approve` |
| SC-007 | screen | `Frappe list and form /desk/ai-job-profile` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §2 roles matrix (every role opened it), §7 P01 |
| DT-006 | doctype | `AI Job Profile Version` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe test suite, §2 roles matrix |
| DT-007 | doctype | `AI Job Question` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe test suite, §2 roles matrix |
| DT-008 | doctype | `AI Job Rule` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe test suite, §2 roles matrix |
| DT-009 | doctype | `AI Recruitment Audit Log` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §10 Frappe `test_hr_decision_needs_a_reason_and_is_logged` |
| SC-008 | screen | `Frappe list and form /desk/ai-recruitment-audit-log` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §2 roles matrix (every role opened it), §7 P01 |
| DT-010 | doctype | `AI Recruitment Job` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| SC-009 | screen | `Frappe list and form /desk/ai-recruitment-job` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §2 roles matrix (every role opened it), §7 P01 |
| DT-011 | doctype | `AI Recruitment Settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §10 Frappe `test_application_is_always_saved` |
| SC-010 | screen | `Frappe form /desk/ai-recruitment-settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-011 | screen | `Frappe form Job Applicant (extended by the app)` | 124 | [S00_home.png](images/steps/S00_home.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-012 | screen | `Frappe form Job Opening (extended by the app)` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-013 | screen | `Frappe list Job Applicant (AI columns)` | 42 | [S08_list.png](images/fit/S08_list.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-014 | screen | `Workspace sidebar "Talent AI"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §2 roles matrix (every role opened it), §7 P01 |
| BT-001 | button | `Sidebar item AI Recruitment → Page ai-recruitment` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-002 | button | `Sidebar item Cycle map → Page talent-ai` | 25 | [S00_cycle_map_1.png](images/steps/S00_cycle_map_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-003 | button | `Sidebar item AI Job Profile → DocType AI Job Profile` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §3 R08 (home page), §2 roles matrix |
| BT-004 | button | `Sidebar item Job Opening → DocType Job Opening` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §3 R08 (home page), §2 roles matrix |
| BT-005 | button | `Sidebar item Job Applicant → DocType Job Applicant` | 42 | [S08_list.png](images/fit/S08_list.png) | §3 R08 (home page), §2 roles matrix |
| BT-006 | button | `Sidebar item AI Batch Monitor → Page ai-batch` | 41 | [S07_batch.png](images/fit/S07_batch.png) | §3 R08 (home page), §2 roles matrix |
| BT-007 | button | `Sidebar item AI Ranking → Page ai-ranking` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §3 R08 (home page), §2 roles matrix |
| BT-008 | button | `Sidebar item AI Talent Pool → Page ai-talent-pool` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §3 R08 (home page), §2 roles matrix |
| BT-009 | button | `Sidebar item AI Recruitment Job → DocType AI Recruitment Job` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §3 R08 (home page), §2 roles matrix |
| BT-010 | button | `Sidebar item AI Candidate Assessment → DocType AI Candidate Assessment` | 43 | [S09_head.png](images/steps/S09_head.png) | §3 R08 (home page), §2 roles matrix |
| BT-011 | button | `Sidebar item AI Recruitment Audit Log → DocType AI Recruitment Audit Log` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §3 R08 (home page), §2 roles matrix |
| BT-012 | button | `Sidebar item AI Recruitment Settings → DocType AI Recruitment Settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §3 R08 (home page), §2 roles matrix |
| SC-015 | screen | `Desktop icon "Talent AI"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §2 roles matrix (every role opened it), §7 P01 |
| SC-016 | screen | `Public page /ai-apply/new` | 34 | [S05_form_1.png](images/steps/S05_form_1.png) | §4 C01–C09 (form), §7 P01 (public pages) |
| SC-017 | screen | `Public job list /jobs (HRMS page, Talent AI requirements added)` | 32 | [S03_jobs.png](images/steps/S03_jobs.png) | §4 C01–C09 (form), §7 P01 (public pages) |
| SC-018 | screen | `Public job page /jobs/<route> (HRMS page, Apply button to the AI form)` | 33 | [S04_job_page.png](images/steps/S04_job_page.png) | §4 C01–C09 (form), §7 P01 (public pages) |
| SC-019 | screen | `Talent Console screen home` | 61 | [C_home.png](images/fit/C_home.png) | §6 N01, K03b, N02 |
| SC-020 | screen | `Talent Console screen apply` | 63 | [C_apply.png](images/fit/C_apply.png) | §6 N01, K03b, N02 |
| SC-021 | screen | `Talent Console screen list` | 65 | [C_list.png](images/fit/C_list.png) | §6 N01, K03b, N02 |
| SC-022 | screen | `Talent Console screen ranking` | 67 | [C_ranking.png](images/fit/C_ranking.png) | §6 N01, K03b, N02 |
| SC-023 | screen | `Talent Console screen profile` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01, K03b, N02 |
| SC-024 | screen | `Talent Console screen processing` | 64 | [C_processing.png](images/steps/C_processing.png) | §6 N01, K03b, N02 |
| SC-025 | screen | `Talent Console screen cv` | 71 | [C_cv.png](images/fit/C_cv.png) | §6 N01, K03b, N02 |
| SC-026 | screen | `Talent Console screen tryfile` | 72 | [C_tryfile.png](images/fit/C_tryfile.png) | §6 N01, K03b, N02 |
| SC-027 | screen | `Talent Console screen jobs` | 68 | [C_jobs.png](images/fit/C_jobs.png) | §6 N01, K03b, N02 |
| SC-028 | screen | `Talent Console screen audit` | 69 | [C_audit.png](images/fit/C_audit.png) | §6 N01, K03b, N02 |
| SC-029 | screen | `Talent Console screen settings` | 70 | [C_settings.png](images/steps/C_settings.png) | §6 N01, K03b, N02 |
| SC-030 | screen | `Talent Console screen applicant` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §6 N01, K03b, N02 |
| SC-031 | screen | `Talent Console screen login` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §6 N01, K03b, N02 |
| BT-013 | button | `Talent Console action go` | 61 | [C_home.png](images/fit/C_home.png) | §6 N01 (console screens) |
| BT-014 | button | `Talent Console action toggleDev` | 73 | [C_dev.png](images/fit/C_dev.png) | §6 N01 (console screens) |
| BT-015 | button | `Talent Console action setLang` | 73 | [C_dev.png](images/fit/C_dev.png) | §6 N01 (console screens) |
| BT-016 | button | `Talent Console action closeModal` | 73 | [C_dev.png](images/fit/C_dev.png) | §6 N01 (console screens) |
| BT-017 | button | `Talent Console action pickJob` | 61 | [C_home.png](images/fit/C_home.png) | §6 N01 (console screens) |
| BT-018 | button | `Talent Console action newJob` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-019 | button | `Talent Console action delCrit` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-020 | button | `Talent Console action delRule` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-021 | button | `Talent Console action delQ` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-022 | button | `Talent Console action useDraft` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-023 | button | `Talent Console action discardDraft` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-024 | button | `Talent Console action aiDraft` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-025 | button | `Talent Console action approveProfile` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-026 | button | `Talent Console action addCrit` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-027 | button | `Talent Console action addRule` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-028 | button | `Talent Console action addQ` | 62 | [C_profile.png](images/fit/C_profile.png) | §6 N01 (console screens) |
| BT-029 | button | `Talent Console action submitForm` | 63 | [C_apply.png](images/fit/C_apply.png) | §6 N01 (console screens) |
| BT-030 | button | `Talent Console action retry` | 64 | [C_processing.png](images/steps/C_processing.png) | §6 N01 (console screens) |
| BT-031 | button | `Talent Console action openApp` | 65 | [C_list.png](images/fit/C_list.png) | §6 N01 (console screens) |
| BT-032 | button | `Talent Console action cvLine` | 71 | [C_cv.png](images/fit/C_cv.png) | §6 N01 (console screens) |
| BT-033 | button | `Talent Console action cvPage` | 71 | [C_cv.png](images/fit/C_cv.png) | §6 N01 (console screens) |
| BT-034 | button | `Talent Console action cvSel` | 71 | [C_cv.png](images/fit/C_cv.png) | §6 N01 (console screens) |
| BT-035 | button | `Talent Console action tryRun` | 72 | [C_tryfile.png](images/fit/C_tryfile.png) | §6 N01 (console screens) |
| BT-036 | button | `Talent Console action rescreenOne` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §6 N01 (console screens) |
| BT-037 | button | `Talent Console action hilite` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §6 N01 (console screens) |
| BT-038 | button | `Talent Console action override` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §6 N01 (console screens) |
| BT-039 | button | `Talent Console action rescreenAll` | 67 | [C_ranking.png](images/fit/C_ranking.png) | §6 N01 (console screens) |
| BT-040 | button | `Talent Console action exportCsv` | 67 | [C_ranking.png](images/fit/C_ranking.png) | §6 N01 (console screens) |
| BT-041 | button | `Talent Console action saveSettings` | 70 | [C_settings.png](images/steps/C_settings.png) | §6 N01 (console screens) |
| BT-042 | button | `Frappe button "إعادة التقييم"` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §5 K07–K14 (desk actions) |
| BT-043 | button | `Frappe button "تحليل السيرة"` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §5 K07–K14 (desk actions) |
| BT-044 | button | `Frappe button "سحب موافقة المعالجة"` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §5 K17 (consent withdrawn) |
| BT-045 | button | `Frappe button "تسجيل الموافقة"` | 102 | [X_paper_awaiting.png](images/steps/X_paper_awaiting.png) | §5 K16 (paper application, consent recorded by HR) |
| BT-046 | button | `Frappe button "ترتيب الشاغر"` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §5 K07–K14 (desk actions) |
| BT-047 | button | `Frappe decision button "ترشيح للمقابلة" (Shortlisted)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §5 K07–K14 (desk actions) |
| BT-048 | button | `Frappe decision button "تعليق" (Hold)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §5 K07–K14 (desk actions) |
| BT-049 | button | `Frappe decision button "رفض" (Rejected)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §5 K07–K14 (desk actions) |
| BT-050 | button | `Frappe button "ملف المعايير"` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §5 K07–K14 (desk actions) |
| BT-051 | button | `Frappe button "إنشاء ملف المعايير"` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §5 K07–K14 (desk actions) |
| BT-052 | button | `Frappe button "ترتيب المتقدمين"` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §5 K07–K14 (desk actions) |
| BT-053 | button | `Frappe button "متابعة المعالجة"` | 41 | [S07_batch.png](images/fit/S07_batch.png) | §5 K07–K14 (desk actions) |
| BT-054 | button | `Frappe button "بنك المتقدمين"` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §5 K07–K14 (desk actions) |
| BT-055 | button | `Frappe in-page action data-tai=consent` | 102 | [X_paper_awaiting.png](images/steps/X_paper_awaiting.png) | §5 K16 (paper application, consent recorded by HR) |
| BT-056 | button | `Frappe in-page action data-tai=rescreen` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §5 K07–K14 (desk actions) |
| BT-057 | button | `Frappe in-page action data-tai=retry` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §5 K07–K14 (desk actions) |
| BT-058 | button | `Frappe in-page action data-tai=hilite` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §5 K07–K14 (desk actions) |
| BT-059 | button | `Frappe in-page action data-tai=override` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §5 K07–K14 (desk actions) |
| BT-060 | button | `Frappe in-page action data-tai=cv` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §5 K07–K14 (desk actions) |
| BT-061 | button | `Frappe in-page action data-tai=decide` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §5 K07–K14 (desk actions) |
| BT-062 | button | `Frappe in-page action data-tai=cvline` | 71 | [C_cv.png](images/fit/C_cv.png) | §5 K07–K14 (desk actions) |
| BT-063 | button | `Frappe in-page action data-tai=cvpage` | 71 | [C_cv.png](images/fit/C_cv.png) | §5 K07–K14 (desk actions) |
| BT-064 | button | `Frappe in-page action data-tai=cvsel` | 71 | [C_cv.png](images/fit/C_cv.png) | §5 K07–K14 (desk actions) |
| BT-065 | button | `Frappe button "فتح المتقدم"` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §5 K07–K14 (desk actions) |
| BT-066 | button | `Frappe button "اعتماد"` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §5 K07–K14 (desk actions) |
| BT-067 | button | `Frappe button "معاينة الأثر"` | 29 | [S01c_impact.png](images/fit/S01c_impact.png) | §5 K07–K14 (desk actions) |
| BT-068 | button | `Frappe button "اقتراح معايير AI"` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §5 K07–K14 (desk actions) |
| BT-069 | button | `Frappe button "نسخ من قالب المسمى الوظيفي"` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §5 K07–K14 (desk actions) |
| BT-070 | button | `Frappe button "إعادة المحاولة"` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §5 K07–K14 (desk actions) |
| BT-071 | button | `Frappe button "تحديث من المحرك"` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §5 K07–K14 (desk actions) |
| BT-072 | button | `Frappe button "مهام الذكاء"` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §5 K07–K14 (desk actions) |
| BT-073 | button | `Frappe button "مقارنة المحددين"` | 50 | [S10b_compare.png](images/fit/S10b_compare.png) | §5 K07–K14 (desk actions) |
| BT-074 | button | `Frappe button "إعادة تقييم القديم والفاشل"` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §5 K07–K14 (desk actions) |
| BT-075 | button | `Frappe button "خريطة الدورة"` | 25 | [S00_cycle_map_1.png](images/steps/S00_cycle_map_1.png) | §5 K07–K14 (desk actions) |
| BT-076 | button | `Home page card 1 "ملف المعايير"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-077 | button | `Home page card 2 "الشواغر"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-078 | button | `Home page card 3 "صفحة التقديم العامة"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-079 | button | `Home page card 4 "قائمة المتقدمين"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-080 | button | `Home page card 5 "الترتيب"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-081 | button | `Home page card 6 "بنك المتقدمين"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-082 | button | `Home page card 7 "مهام الذكاء"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-083 | button | `Home page card 8 "الإعدادات"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| BT-084 | button | `Home page card 9 "سجل التدقيق"` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §3 R08 (home page), §2 roles matrix |
| FD-001 | field | `Job Opening.ai_enabled (Check)` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-002 | field | `Job Opening.ai_profile (Link)` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §10 Frappe `test_opening_points_the_apply_button_to_the_ai_form` |
| FD-003 | field | `Job Opening.ai_profile_approved (Check)` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §10 Frappe `test_opening_points_the_apply_button_to_the_ai_form` |
| FD-004 | field | `Job Opening.ai_links (HTML)` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §10 Frappe `test_ai_section_is_on_the_main_tab_of_the_opening` |
| FD-005 | field | `Job Applicant.nationality (Link)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_missing_required_answer_and_consent_are_refused` |
| FD-006 | field | `Job Applicant.date_of_birth (Date)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_missing_required_answer_and_consent_are_refused` |
| FD-007 | field | `Job Applicant.id_type (Select)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_application_is_always_saved` |
| FD-008 | field | `Job Applicant.national_id (Data)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| FD-009 | field | `Job Applicant.height_cm (Int)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| FD-010 | field | `Job Applicant.weight_kg (Int)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 engine `test_settings_engine_owned` |
| FD-011 | field | `Job Applicant.ai_consent (Check)` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §10 Frappe `test_missing_required_answer_and_consent_are_refused` |
| FD-012 | field | `Job Applicant.ai_consent_version (Data)` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| FD-013 | field | `Job Applicant.ai_consent_on (Datetime)` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| FD-014 | field | `Job Applicant.ai_consent_source (Small Text)` | 104 | [X_paper_dialog.png](images/steps/X_paper_dialog.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| FD-015 | field | `Job Applicant.ai_consent_recorded_by (Link)` | 104 | [X_paper_dialog.png](images/steps/X_paper_dialog.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| FD-016 | field | `Job Applicant.ai_consent_withdrawn_on (Datetime)` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| FD-017 | field | `Job Applicant.ai_erased_on (Datetime)` | 108 | [X_withdrawn_applicant.png](images/steps/X_withdrawn_applicant.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FD-018 | field | `Job Applicant.ai_answers (Table)` | 39 | [S05b_answers_grid.png](images/steps/S05b_answers_grid.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| FD-019 | field | `Job Applicant.ai_html (HTML)` | 43 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_ai_fields_are_hr_only` |
| FD-020 | field | `Job Applicant.ai_status (Select)` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| FD-021 | field | `Job Applicant.ai_score (Float)` | 42 | [S08_list.png](images/fit/S08_list.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status` |
| FD-022 | field | `Job Applicant.ai_band (Select)` | 42 | [S08_list.png](images/fit/S08_list.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FD-023 | field | `Job Applicant.ai_eligibility (Select)` | 42 | [S08_list.png](images/fit/S08_list.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-024 | field | `Job Applicant.ai_coverage (Percent)` | 43 | [S09_head.png](images/steps/S09_head.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-025 | field | `Job Applicant.ai_rank (Int)` | 42 | [S08_list.png](images/fit/S08_list.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FD-026 | field | `Job Applicant.ai_assessment (Link)` | 43 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_ai_fields_are_hr_only` |
| FD-027 | field | `Job Applicant.ai_evaluated_on (Datetime)` | 43 | [S09_head.png](images/steps/S09_head.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-028 | field | `Job Applicant.ai_stale (Check)` | 42 | [S08_list.png](images/fit/S08_list.png) | §10 Frappe `test_edit_after_evaluation_makes_the_result_stale` |
| FD-029 | field | `Job Applicant.ai_duplicate_of (Link)` | 42 | [S08_list.png](images/fit/S08_list.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FD-030 | field | `Job Applicant.ai_cv_note (Small Text)` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 Frappe `test_application_is_always_saved` |
| FD-031 | field | `Job Applicant.ai_flags (Small Text)` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-032 | field | `Job Applicant.ai_candidate_ref (Data)` | 124 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| FD-033 | field | `Job Applicant.ai_data_hash (Data)` | 100 | [K07_stale_banner.png](images/test/K07_stale_banner.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| FD-034 | field | `Job Applicant.ai_cv_sha (Data)` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 Frappe `test_text_cv_is_sent_as_bytes_and_cv_problems_never_fail` |
| FD-035 | field | `Job Applicant.ai_decision_reason (Small Text)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §3–7 browser K09 |
| FD-036 | field | `Job Applicant.ai_decided_by (Link)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §10 Frappe `test_hr_decision_needs_a_reason_and_is_logged` |
| FD-037 | field | `Job Applicant.ai_decided_on (Datetime)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §2 roles probes (`rest_applicant`), §5 K01–K15 |
| EP-001 | endpoint | `/api/method/ido_talent_ai.api.apply` | 34 | [S05_form_1.png](images/steps/S05_form_1.png) | §10 Frappe `test_missing_required_answer_and_consent_are_refused` |
| EP-002 | endpoint | `/api/method/ido_talent_ai.api.job_requirements` | 33 | [S04_job_page.png](images/steps/S04_job_page.png) | §10 Frappe `test_opening_points_the_apply_button_to_the_ai_form` |
| EP-003 | endpoint | `/api/method/ido_talent_ai.api.receive_result` | 43 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_callback_signature` |
| EP-004 | endpoint | `/api/method/ido_talent_ai.api.get_assessment` | 43 | [S09_head.png](images/steps/S09_head.png) | §3–7 browser R09 |
| EP-005 | endpoint | `/api/method/ido_talent_ai.api.decide` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §10 Frappe `test_hr_decision_needs_a_reason_and_is_logged` |
| EP-006 | endpoint | `/api/method/ido_talent_ai.api.override` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §3–7 browser K08 |
| EP-007 | endpoint | `/api/method/ido_talent_ai.api.rescreen` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §3–7 browser K07 |
| EP-008 | endpoint | `/api/method/ido_talent_ai.api.retry_job` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §2 roles probes |
| EP-009 | endpoint | `/api/method/ido_talent_ai.api.rescreen_all` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| EP-010 | endpoint | `/api/method/ido_talent_ai.api.ranking` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §10 Frappe `test_ai_fields_are_hr_only` |
| EP-011 | endpoint | `/api/method/ido_talent_ai.api.export_ranking_csv` | 51 | [S10c_csv.png](images/steps/S10c_csv.png) | §3–7 browser K10 |
| EP-012 | endpoint | `/api/method/ido_talent_ai.api.compare` | 50 | [S10b_compare.png](images/fit/S10b_compare.png) | §3–7 browser K11 |
| EP-013 | endpoint | `/api/method/ido_talent_ai.api.batch_status` | 41 | [S07_batch.png](images/fit/S07_batch.png) | §10 Frappe `test_the_safety_nets_read_the_site_clock` |
| EP-014 | endpoint | `/api/method/ido_talent_ai.api.home_counts` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §10 Frappe `test_hr_users_land_on_the_home_page_in_arabic` |
| EP-015 | endpoint | `/api/method/ido_talent_ai.api.openings` | 25 | [S00_cycle_map_1.png](images/steps/S00_cycle_map_1.png) | §2 roles probes |
| EP-016 | endpoint | `/api/method/ido_talent_ai.api.talent_pool` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §10 Frappe `test_talent_pool_names_suggestions_and_exclusions` |
| EP-017 | endpoint | `/api/method/ido_talent_ai.api.withdraw_consent` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| EP-018 | endpoint | `/api/method/ido_talent_ai.api.record_consent` | 104 | [X_paper_dialog.png](images/steps/X_paper_dialog.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| EP-019 | endpoint | `/api/method/ido_talent_ai.api.cv_analysis` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §3–7 browser C01–C09 |
| EP-020 | endpoint | `/api/method/ido_talent_ai.api.cv_page` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §2 roles probes |
| EP-021 | endpoint | `/api/method/ido_talent_ai.api.engine_settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §3–7 browser K15 |
| EP-022 | endpoint | `/api/method/ido_talent_ai.api.i_am_hr` | 124 | [E_docs.png](images/steps/E_docs.png) | §2 roles probes |
| EP-023 | endpoint | `/api/method/ido_talent_ai.profile.approve` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe `test_weights_must_total_100_to_approve` |
| EP-024 | endpoint | `/api/method/ido_talent_ai.profile.impact_preview` | 29 | [S01c_impact.png](images/fit/S01c_impact.png) | §3–7 browser K14 |
| EP-025 | endpoint | `/api/method/ido_talent_ai.profile.draft_criteria` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §2 roles probes |
| EP-026 | endpoint | `/api/method/ido_talent_ai.profile.templates_for` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §2 roles probes |
| EP-027 | endpoint | `/api/method/ido_talent_ai.profile.copy_from_template` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §2 roles probes |
| EP-028 | endpoint | `/api/method/ido_talent_ai.talent_ai.doctype.ai_recruitment_settings.ai_recruitment_settings.refresh_from_engine` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §2 roles probes |
| HK-001 | hook | `doc event after_insert → ido_talent_ai.screening.on_applicant_insert` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §3–7 browser checks |
| HK-002 | hook | `doc event on_update → ido_talent_ai.screening.on_applicant_update` | 48 | [S09f_decision_card.png](images/steps/S09f_decision_card.png) | §3–7 browser checks |
| HK-003 | hook | `doc event on_trash → ido_talent_ai.screening.on_applicant_trash` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §3–7 browser checks |
| HK-004 | hook | `doc event validate → ido_talent_ai.screening.on_opening_validate` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §3–7 browser checks |
| HK-005 | hook | `doc event on_trash → ido_talent_ai.screening.on_opening_trash` | 31 | [S02_opening_ai.png](images/steps/S02_opening_ai.png) | §3–7 browser checks |
| HK-006 | hook | `scheduled job ido_talent_ai.screening.sync_running_jobs` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §3–7 browser checks |
| HK-007 | hook | `scheduled job ido_talent_ai.screening.queue_missing` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_the_safety_nets_read_the_site_clock` |
| HK-008 | hook | `scheduled job ido_talent_ai.screening.erase_pending` | 108 | [X_withdrawn_applicant.png](images/steps/X_withdrawn_applicant.png) | §10 Frappe `test_withdrawal_while_the_engine_is_down_is_erased_later` |
| HK-009 | hook | `scheduled job ido_talent_ai.screening.retry_failed_jobs` | 41 | [S07_batch.png](images/fit/S07_batch.png) | §3–7 browser checks |
| HK-010 | hook | `login hook → "التوظيف الذكي" for HR roles` | 23 | [S00_home_1.png](images/steps/S00_home_1.png) | §10 Frappe `test_hr_users_land_on_the_home_page_in_arabic` |
| EP-029 | endpoint | `GET /v1/audit` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §10 engine `test_override_requires_reason_and_recomputes` |
| EP-030 | endpoint | `GET /v1/candidates` | 65 | [C_list.png](images/fit/C_list.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-031 | endpoint | `PUT /v1/candidates/{ref}` | 63 | [C_apply.png](images/fit/C_apply.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-032 | endpoint | `GET /v1/candidates/{ref}` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-033 | endpoint | `DELETE /v1/candidates/{ref}` | 66 | [C_applicant.png](images/fit/C_applicant.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-034 | endpoint | `GET /console` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-035 | endpoint | `GET /console/login` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-036 | endpoint | `POST /console/login` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-037 | endpoint | `POST /console/logout` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-038 | endpoint | `GET /console/me` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-039 | endpoint | `POST /console/id-token` | 63 | [C_apply.png](images/fit/C_apply.png) | §10 engine `test_id_token_helper_matches_hmac_and_needs_login` |
| EP-040 | endpoint | `GET /console/static/{path:path}` | 73 | [C_dev.png](images/fit/C_dev.png) | §10 engine `test_console_requires_login_and_hides_the_api_key` |
| EP-041 | endpoint | `GET /console/health` | 73 | [C_dev.png](images/fit/C_dev.png) | §10 engine API tests |
| EP-042 | endpoint | `PUT /v1/candidates/{ref}/cv` | 63 | [C_apply.png](images/fit/C_apply.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-043 | endpoint | `GET /v1/candidates/{ref}/cv` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-044 | endpoint | `GET /v1/candidates/{ref}/cv/file` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §10 engine `test_api_cv_layout_pages_file_and_quote_boxes` |
| EP-045 | endpoint | `GET /v1/candidates/{ref}/cv/pages/{page}` | 46 | [S09d_cvtext.png](images/steps/S09d_cvtext.png) | §10 engine `test_api_cv_layout_pages_file_and_quote_boxes` |
| EP-046 | endpoint | `DELETE /v1/candidates/{ref}/cv` | 124 | [E_docs.png](images/steps/E_docs.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| EP-047 | endpoint | `POST /v1/documents/inspect` | 72 | [C_tryfile.png](images/fit/C_tryfile.png) | §10 engine `test_inspect_stores_nothing` |
| EP-048 | endpoint | `GET /health` | 74 | [E_docs.png](images/fit/E_docs.png) | §10 engine `test_auth_required` |
| EP-049 | endpoint | `GET /ready` | 74 | [E_docs.png](images/fit/E_docs.png) | §10 engine `test_auth_required` |
| EP-050 | endpoint | `POST /v1/jobs/draft-criteria` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §10 engine `test_draft_criteria_sums_to_100` |
| EP-051 | endpoint | `GET /v1/jobs` | 61 | [C_home.png](images/fit/C_home.png) | §10 engine `test_auth_required` |
| EP-052 | endpoint | `PUT /v1/jobs/{ref}` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 engine `test_weights_must_total_100` |
| EP-053 | endpoint | `GET /v1/jobs/{ref}` | 61 | [C_home.png](images/fit/C_home.png) | §10 engine `test_weights_must_total_100` |
| EP-054 | endpoint | `DELETE /v1/jobs/{ref}` | 62 | [C_profile.png](images/fit/C_profile.png) | §10 engine `test_weights_must_total_100` |
| EP-055 | endpoint | `GET /v1/jobs/{ref}/ranking` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §10 engine `test_full_cycle_matches_the_demo` |
| EP-056 | endpoint | `POST /v1/jobs/{ref}/impact` | 29 | [S01c_impact.png](images/fit/S01c_impact.png) | §10 engine `test_impact_preview_keeps_levels_and_moves_weights` |
| EP-057 | endpoint | `POST /v1/jobs/{ref}/rescreen` | 49 | [S10_ranking.png](images/fit/S10_ranking.png) | §10 engine `test_new_profile_version_makes_results_stale_and_rescreen_updates` |
| EP-058 | endpoint | `POST /v1/screenings` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 engine `test_worked_example_details` |
| EP-059 | endpoint | `GET /v1/screenings` | 65 | [C_list.png](images/fit/C_list.png) | §10 engine `test_worked_example_details` |
| EP-060 | endpoint | `GET /v1/screenings/{screening_id}` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 engine `test_worked_example_details` |
| EP-061 | endpoint | `POST /v1/screenings/{screening_id}/override` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §10 engine `test_override_requires_reason_and_recomputes` |
| EP-062 | endpoint | `POST /v1/screenings/{screening_id}/retry` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §10 engine `test_engine_failure_becomes_failed_after_retries_then_retry_works` |
| EP-063 | endpoint | `GET /v1/settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §10 engine `test_settings_engine_owned` |
| EP-064 | endpoint | `PUT /v1/settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §10 engine `test_settings_engine_owned` |
| EP-065 | endpoint | `POST /v1/talent-pool/search` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §10 Frappe `test_talent_pool_names_suggestions_and_exclusions` |
| EP-066 | endpoint | `GET /v1/talent-pool/status` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §10 engine `test_talent_pool_rules_first_then_similarity_with_exclusions` |
| EP-067 | endpoint | `POST /v1/talent-pool/reindex` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §10 engine API tests |
| SG-001 | stage | `stage intake — Intake` | 75 | [S06_stage_01.png](images/steps/S06_stage_01.png) | §3–7 browser checks |
| SG-002 | stage | `stage answers — Read form answers` | 76 | [S06_stage_02.png](images/steps/S06_stage_02.png) | §10 Frappe `test_missing_required_answer_and_consent_are_refused` |
| SG-003 | stage | `stage cv_text — Extract CV text` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_upload_replaces_stale_and_shows_in_screening` |
| SG-004 | stage | `stage redaction — Redaction` | 78 | [S06_stage_04.png](images/steps/S06_stage_04.png) | §10 engine `test_upload_replaces_stale_and_shows_in_screening` |
| SG-005 | stage | `stage profile — Structured profile` | 79 | [S06_stage_05.png](images/steps/S06_stage_05.png) | §10 engine `test_upload_replaces_stale_and_shows_in_screening` |
| SG-006 | stage | `stage evidence_check — Evidence check` | 80 | [S06_stage_06.png](images/steps/S06_stage_06.png) | §10 engine `test_local_provider_full_cycle` |
| SG-007 | stage | `stage eligibility — Hard eligibility rules` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SG-008 | stage | `stage judgement — Criteria judgement` | 82 | [S06_stage_08.png](images/steps/S06_stage_08.png) | §10 engine `test_local_provider_full_cycle` |
| SG-009 | stage | `stage scoring — Score and rank` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §3–7 browser K14 |
| SG-010 | stage | `stage index — Index` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_invalid_json_repaired_once_then_fails` |
| FL-001 | flag | `flag missing_evidence — Missing evidence` | 76 | [S06_stage_02.png](images/steps/S06_stage_02.png) | §10 engine `test_blank_vs_zero_and_needs_review` |
| FL-002 | flag | `flag mandatory_missing — Mandatory criterion without evidence` | 82 | [S06_stage_08.png](images/steps/S06_stage_08.png) | §10 engine `test_blank_vs_zero_and_needs_review` |
| FL-003 | flag | `flag mandatory_zero — Mandatory criterion at level 0` | 82 | [S06_stage_08.png](images/steps/S06_stage_08.png) | §10 engine `test_blank_vs_zero_and_needs_review` |
| FL-004 | flag | `flag low_coverage — Low coverage` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §10 engine `test_blank_vs_zero_and_needs_review` |
| FL-005 | flag | `flag contradiction — Answer contradicts the CV` | 82 | [S06_stage_08.png](images/steps/S06_stage_08.png) | §10 engine `test_contradiction_uses_lower_level_and_needs_review` |
| FL-006 | flag | `flag evidence_mismatch — Evidence does not match the stored answer` | 80 | [S06_stage_06.png](images/steps/S06_stage_06.png) | §10 engine `test_form_value_tolerance_and_question_from_job` |
| FL-007 | flag | `flag cv_unreadable — CV file unreadable` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_corrupt_cv_never_fails_the_screening` |
| FL-008 | flag | `flag low_ocr_confidence — Low OCR confidence` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_low_ocr_confidence_needs_review` |
| FL-009 | flag | `flag redaction_guard — Redaction guard removed leftover data` | 78 | [S06_stage_04.png](images/steps/S06_stage_04.png) | §3–7 browser checks |
| FL-010 | flag | `flag duplicate — Duplicate application` | 100 | [K07_stale_banner.png](images/test/K07_stale_banner.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FL-011 | flag | `flag stale — Stale — previous criteria version` | 100 | [K07_stale_banner.png](images/test/K07_stale_banner.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| FL-012 | flag | `flag data_changed — Result does not reflect the latest edit` | 100 | [K07_stale_banner.png](images/test/K07_stale_banner.png) | §10 Frappe `test_edit_after_evaluation_makes_the_result_stale` |
| FL-013 | flag | `flag hr_override — HR override` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §10 engine `test_override_requires_reason_and_recomputes` |
| SS-001 | status | `screening status queued → ai_status Processing` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| SS-002 | status | `screening status processing → ai_status Processing` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| SS-003 | status | `screening status completed → ai_status Completed` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SS-004 | status | `screening status needs_review → ai_status Needs Review` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status` |
| SS-005 | status | `screening status failed → ai_status Failed` | 40 | [S06_stages.png](images/steps/S06_stages.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-006 | status | `band high — High` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-007 | status | `band medium — Medium` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SS-008 | status | `band low — Low` | 83 | [S06_stage_09.png](images/steps/S06_stage_09.png) | §10 engine `test_blank_vs_zero_and_needs_review` |
| SS-009 | status | `eligibility eligible — Eligible` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SS-010 | status | `eligibility not_eligible — Not eligible (as declared)` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-011 | status | `eligibility needs_review — Needs review` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status` |
| SS-012 | status | `ranking group duplicate — Duplicate — only the original application is ranked` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-013 | status | `ranking group processing — Processing` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| SS-014 | status | `ranking group failed — Processing failed` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-015 | status | `ranking group stale — Stale — previous criteria version` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-016 | status | `ranking group data_changed — Result does not reflect the latest edit` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_edit_after_evaluation_makes_the_result_stale` |
| SS-017 | status | `ranking group not_eligible — Not eligible (as declared)` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-018 | status | `ranking group needs_review — Missing value, low coverage or contradiction` | 52 | [S10f_groups.png](images/steps/S10f_groups.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status` |
| SS-019 | status | `ranking group consent_withdrawn — Excluded: consent withdrawn — the AI data was erased` | 107 | [X_withdrawn_group.png](images/steps/X_withdrawn_group.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-020 | status | `HR decision Shortlisted (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §10 Frappe `test_hr_decision_needs_a_reason_and_is_logged` |
| SS-021 | status | `HR decision Hold (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §3–7 browser K09 |
| SS-022 | status | `HR decision Rejected (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §10 Frappe `test_hr_decision_needs_a_reason_and_is_logged` |
| SS-023 | status | `HR decision Open (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| SS-024 | status | `HR decision Replied (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §3–7 browser checks |
| SS-025 | status | `HR decision Accepted (Job Applicant.status)` | 47 | [S09e_decision_dialog.png](images/steps/S09e_decision_dialog.png) | §3–7 browser checks |
| SS-026 | status | `Job Applicant ai_status Awaiting Consent (set by Frappe)` | 102 | [X_paper_awaiting.png](images/steps/X_paper_awaiting.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| SS-027 | status | `Job Applicant ai_status Consent Withdrawn (set by Frappe)` | 107 | [X_withdrawn_group.png](images/steps/X_withdrawn_group.png) | §10 Frappe `test_withdrawn_consent_leaves_the_ranking_and_erases_the_ai_data` |
| SS-028 | status | `ranking group awaiting_consent (built by Frappe)` | 103 | [X_awaiting_group.png](images/steps/X_awaiting_group.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| SS-029 | status | `AI Recruitment Job status Queued` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| SS-030 | status | `AI Recruitment Job status Running` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §3–7 browser checks |
| SS-031 | status | `AI Recruitment Job status Completed` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status` |
| SS-032 | status | `AI Recruitment Job status Failed` | 54 | [S12_jobs.png](images/fit/S12_jobs.png) | §10 Frappe `test_application_saved_with_all_answers_even_if_engine_down` |
| SS-033 | status | `AI Recruitment Job status Cancelled` | 108 | [X_withdrawn_applicant.png](images/steps/X_withdrawn_applicant.png) | §10 Frappe `test_withdrawal_while_the_engine_is_down_is_erased_later` |
| SE-001 | setting | `AI Recruitment Settings.enabled (Check)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §10 Frappe `test_application_is_always_saved` |
| SE-002 | setting | `AI Recruitment Settings.auto_screen_on_apply (Check)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §3–7 browser checks |
| SE-003 | setting | `AI Recruitment Settings.engine_url (Data)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §3–7 browser checks |
| SE-004 | setting | `AI Recruitment Settings.api_key (Password)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §10 engine `test_api_key_hash_is_stable` |
| SE-005 | setting | `AI Recruitment Settings.request_timeout (Int)` | 101 | [K15_failed.png](images/test/K15_failed.png) | §3–7 browser checks |
| SE-006 | setting | `AI Recruitment Settings.callback_url (Data)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §10 engine `test_callback_is_signed_and_delivered` |
| SE-007 | setting | `AI Recruitment Settings.callback_secret (Password)` | 124 | [S13_settings.png](images/steps/S13_settings.png) | §10 Frappe `test_callback_signature` |
| SE-008 | setting | `AI Recruitment Settings.id_token_secret (Password)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §10 engine `test_id_token_helper_matches_hmac_and_needs_login` |
| SE-009 | setting | `AI Recruitment Settings.provider (Select)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §10 engine `test_settings_engine_owned` |
| SE-010 | setting | `AI Recruitment Settings.model (Data)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SE-011 | setting | `AI Recruitment Settings.judge_prompt (Data)` | 82 | [S06_stage_08.png](images/steps/S06_stage_08.png) | §3–7 browser checks |
| SE-012 | setting | `AI Recruitment Settings.ocr_provider (Select)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §10 engine `test_settings_show_ocr_readiness` |
| SE-013 | setting | `AI Recruitment Settings.timeout (Int)` | 101 | [K15_failed.png](images/test/K15_failed.png) | §3–7 browser K03a |
| SE-014 | setting | `AI Recruitment Settings.max_retries (Int)` | 101 | [K15_failed.png](images/test/K15_failed.png) | §10 engine `test_settings_engine_owned` |
| SE-015 | setting | `AI Recruitment Settings.last_synced (Datetime)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §3–7 browser checks |
| SE-016 | setting | `AI Recruitment Settings.allowed_facts (Small Text)` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 engine `test_settings_engine_owned` |
| SE-017 | setting | `AI Recruitment Settings.retention_days (Int)` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_applied_at_orders_duplicates_and_starts_retention` |
| SE-018 | setting | `AI Recruitment Settings.consent_version (Data)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §10 Frappe `test_paper_application_waits_until_hr_records_the_consent` |
| SE-019 | setting | `AI Recruitment Settings.consent_text (Small Text)` | 125 | [S13_settings.png](images/steps/S13_settings.png) | §3–7 browser checks |
| SE-020 | setting | `engine .env APP_ENV` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-021 | setting | `engine .env LOG_LEVEL` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-022 | setting | `engine .env TZ` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-023 | setting | `engine .env API_PORT` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-024 | setting | `engine .env API_BIND_TAILSCALE` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-025 | setting | `engine .env DB_HOST_PORT` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-026 | setting | `engine .env REDIS_HOST_PORT` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-027 | setting | `engine .env POSTGRES_USER` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-028 | setting | `engine .env POSTGRES_PASSWORD` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-029 | setting | `engine .env POSTGRES_DB` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-030 | setting | `engine .env REDIS_PASSWORD` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-031 | setting | `engine .env TENANT_API_KEY` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-032 | setting | `engine .env CALLBACK_SECRET` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-033 | setting | `engine .env DATABASE_URL` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-034 | setting | `engine .env REDIS_URL` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-035 | setting | `engine .env QUEUE_MODE` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-036 | setting | `engine .env AI_PROVIDER` | 79 | [S06_stage_05.png](images/steps/S06_stage_05.png) | §10 engine `test_every_env_key_is_used` |
| SE-037 | setting | `engine .env LLM_BASE_URL` | 79 | [S06_stage_05.png](images/steps/S06_stage_05.png) | §10 engine `test_every_env_key_is_used` |
| SE-038 | setting | `engine .env LLM_MODEL` | 79 | [S06_stage_05.png](images/steps/S06_stage_05.png) | §10 engine `test_every_env_key_is_used` |
| SE-039 | setting | `engine .env VLLM_MODEL` | 79 | [S06_stage_05.png](images/steps/S06_stage_05.png) | §10 engine `test_every_env_key_is_used` |
| SE-040 | setting | `engine .env VLLM_IMAGE_TAG` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-041 | setting | `engine .env VLLM_MAX_MODEL_LEN` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-042 | setting | `engine .env VLLM_MAX_NUM_SEQS` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-043 | setting | `engine .env LLM_TIMEOUT_S` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-044 | setting | `engine .env LLM_MAX_RETRIES` | 125 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-045 | setting | `engine .env VLLM_GPU_MEMORY_UTILIZATION` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-046 | setting | `engine .env CLOUD_LLM_BASE_URL` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-047 | setting | `engine .env CLOUD_LLM_MODEL` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-048 | setting | `engine .env CLOUD_LLM_API_KEY` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-049 | setting | `engine .env OCR_PROVIDER` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_every_env_key_is_used` |
| SE-050 | setting | `engine .env OCR_THREADS` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_every_env_key_is_used` |
| SE-051 | setting | `engine .env MAX_UPLOAD_MB` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_every_env_key_is_used` |
| SE-052 | setting | `engine .env OCR_MIN_CONFIDENCE` | 77 | [S06_stage_03.png](images/steps/S06_stage_03.png) | §10 engine `test_every_env_key_is_used` |
| SE-053 | setting | `engine .env EMBEDDING_MODEL` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_every_env_key_is_used` |
| SE-054 | setting | `engine .env EMBEDDING_PROVIDER` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_every_env_key_is_used` |
| SE-055 | setting | `engine .env EMBEDDING_BASE_URL` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_every_env_key_is_used` |
| SE-056 | setting | `engine .env FILE_STORE` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-057 | setting | `engine .env RETENTION_DAYS_DEFAULT` | 84 | [S06_stage_10.png](images/steps/S06_stage_10.png) | §10 engine `test_every_env_key_is_used` |
| SE-058 | setting | `engine .env MAX_ATTEMPTS` | 101 | [K15_failed.png](images/test/K15_failed.png) | §10 engine `test_every_env_key_is_used` |
| SE-059 | setting | `engine .env TENANT_NAME` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-060 | setting | `engine .env ALLOWED_FACTS` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 engine `test_every_env_key_is_used` |
| SE-061 | setting | `engine .env CONSOLE_USER` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-062 | setting | `engine .env CONSOLE_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-063 | setting | `engine .env CONSOLE_SESSION_SECRET` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-064 | setting | `engine .env CONSOLE_ID_TOKEN_SECRET` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-065 | setting | `engine .env CALLBACK_URL` | 126 | [env_keys.png](images/terminal/env_keys.png) | §10 engine `test_every_env_key_is_used` |
| SE-066 | setting | `dev bench .env DB_ROOT_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-067 | setting | `dev bench .env ADMIN_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-068 | setting | `dev bench .env TAILSCALE_IP` | 126 | [env_keys.png](images/terminal/env_keys.png) | §11 `reset_demo.sh` |
| SE-069 | setting | `dev bench .env SITE` | 126 | [env_keys.png](images/terminal/env_keys.png) | §11 `reset_demo.sh` |
| SE-070 | setting | `dev bench .env HR_MANAGER_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-071 | setting | `dev bench .env HR_USER_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-072 | setting | `dev bench .env EMPLOYEE_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-073 | setting | `dev bench .env INTERVIEWER_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-074 | setting | `dev bench .env ESS_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-075 | setting | `dev bench .env SYSTEM_MANAGER_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-076 | setting | `dev bench .env PORTAL_PASSWORD` | 126 | [env_keys.png](images/terminal/env_keys.png) | §3 R08 (logins) and §11 `init_env.sh` |
| SE-077 | setting | `site config talent_ai_apply_limit (public form rate limit)` | 34 | [S05_form_1.png](images/steps/S05_form_1.png) | §3–7 browser checks |
| RL-001 | role | `role HR Manager (AI fields at permission level 1)` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-002 | role | `role HR User (AI fields at permission level 1)` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-003 | role | `role System Manager (AI fields at permission level 1)` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-004 | role | `demo user hr.manager@example.com (HR Manager, HR User, Employee)` | 14 | [hr_manager_assessment.png](images/fit/hr_manager_assessment.png) | §2 roles matrix and probes |
| RL-005 | role | `demo user hr.user@example.com (HR User, Employee)` | 15 | [refusal_hr_user_settings.png](images/fit/refusal_hr_user_settings.png) | §2 roles matrix and probes |
| RL-006 | role | `demo user employee@example.com (Employee)` | 17 | [refusal_employee_profile.png](images/fit/refusal_employee_profile.png) | §2 roles matrix and probes |
| RL-007 | role | `demo user interviewer@example.com (Interviewer, Employee)` | 16 | [refusal_interviewer_profile.png](images/fit/refusal_interviewer_profile.png) | §2 roles matrix and probes |
| RL-008 | role | `demo user ess@example.com (Employee Self Service)` | 18 | [refusal_ess_profile.png](images/fit/refusal_ess_profile.png) | §2 roles matrix and probes |
| RL-009 | role | `demo user sysmanager@example.com (System Manager)` | 13 | [system_manager_settings.png](images/fit/system_manager_settings.png) | §2 roles matrix and probes |
| RL-010 | role | `demo user portal.applicant@example.com (Website User)` | 19 | [refusal_portal_home.png](images/fit/refusal_portal_home.png) | §2 roles matrix and probes |
| RL-011 | role | `role Administrator` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-012 | role | `role Interviewer` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-013 | role | `role Employee` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-014 | role | `role Employee Self Service` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-015 | role | `role Guest` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| RL-016 | role | `role Website User` | 11 | [hr_manager_home.png](images/roles/hr_manager_home.png) | §2 roles matrix and probes |
| CM-001 | command | `make builder-check` | 126 | [commands.png](images/terminal/commands.png) | §11 `make builder-check` (ok) |
| CM-002 | command | `make build` | 126 | [commands.png](images/terminal/commands.png) | §11 `make -n build` (dry run ok; built for real this round (default builder)) |
| CM-003 | command | `make env` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n env` (dry run ok) |
| CM-004 | command | `make install` | 127 | [commands.png](images/terminal/commands.png) | §11 `make install` (ok) |
| CM-005 | command | `make test` | 127 | [commands.png](images/terminal/commands.png) | §11 `make test` (ok) |
| CM-006 | command | `make lint` | 127 | [commands.png](images/terminal/commands.png) | §11 `make lint` (ok) |
| CM-007 | command | `make fmt` | 127 | [commands.png](images/terminal/commands.png) | §11 `make fmt` (ok) |
| CM-008 | command | `make typecheck` | 127 | [commands.png](images/terminal/commands.png) | §11 `make typecheck` (ok) |
| CM-009 | command | `make up` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n up` (dry run ok) |
| CM-010 | command | `make down` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n down` (dry run ok) |
| CM-011 | command | `make logs` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n logs` (dry run ok) |
| CM-012 | command | `make llm-logs` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n llm-logs` (dry run ok) |
| CM-013 | command | `make gpu` | 127 | [commands.png](images/terminal/commands.png) | §11 `make gpu` (ok) |
| CM-014 | command | `make ps` | 127 | [commands.png](images/terminal/commands.png) | §11 `make ps` (ok) |
| CM-015 | command | `make migrate` | 127 | [commands.png](images/terminal/commands.png) | §11 `make migrate` (ok) |
| CM-016 | command | `make revision` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n revision` (dry run ok) |
| CM-017 | command | `make seed` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n seed` (dry run ok) |
| CM-018 | command | `make cvs` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n cvs` (dry run ok) |
| CM-019 | command | `make receiver` | 127 | [commands.png](images/terminal/commands.png) | §11 `make -n receiver` (dry run ok) |
| CM-020 | command | `talent-engine/scripts/callback_receiver.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/callback_receiver.py` (run in phase 1 (HMAC callback verified)) |
| CM-021 | command | `talent-engine/scripts/cv_texts.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/cv_texts.py` (run in phase 2) |
| CM-022 | command | `talent-engine/scripts/init_env.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/init_env.py` (run in phase 1 (`make env`)) |
| CM-023 | command | `talent-engine/scripts/make_cvs.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/make_cvs.py` (run in phase 2 (`make cvs`)) |
| CM-024 | command | `talent-engine/scripts/reprocess_cvs.py` | 78 | [S06_stage_04.png](images/steps/S06_stage_04.png) | §11 commands |
| CM-025 | command | `talent-engine/scripts/seed.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/seed.py` (run in phase 1 (`make seed`)) |
| CM-026 | command | `talent-engine/scripts/seed_data.py` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/seed_data.py` (run in phase 1) |
| CM-027 | command | `talent-engine/scripts/compose.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/scripts/compose.sh` (run in round 2: restart of api and workers) |
| CM-028 | command | `dev-frappe/clean_install.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `dev-frappe/clean_install.sh` (run in phase 7 (clean install rehearsal)) |
| CM-029 | command | `dev-frappe/init_env.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `dev-frappe/init_env.sh` (run in round 2: extra test-user passwords added) |
| CM-030 | command | `dev-frappe/reset_demo.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `dev-frappe/reset_demo.sh` (run in round 2: demo rebuilt (25 applicants)) |
| CM-031 | command | `dev-frappe/setup.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `dev-frappe/setup.sh` (run in round 2: run inside reset_demo (site setup)) |
| CM-032 | command | `dev-frappe/start.sh` | 127 | [commands.png](images/terminal/commands.png) | §11 `dev-frappe/start.sh` (run in round 2: bench restarted twice) |
| CM-033 | command | `tools/ui/acceptance.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/acceptance.py` (run in phase 7 (docs/ACCEPTANCE_REPORT.md)) |
| CM-034 | command | `tools/ui/apply_via_form.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/apply_via_form.py` (run in round 2: applicant 2017 through the real form) |
| CM-035 | command | `tools/ui/design_audit.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/design_audit.py` (run in round 2: 3 design audits) |
| CM-036 | command | `tools/ui/design_pairs.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/design_pairs.py` (run in round 2: before/after pairs) |
| CM-037 | command | `tools/ui/desk_shots.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/desk_shots.py` (run in phase 6) |
| CM-038 | command | `tools/ui/frappe_ui.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/frappe_ui.py` (run in phases 6–8 (CDP driver of the older tools)) |
| CM-039 | command | `tools/ui/full_test.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/full_test.py` (run in round 2: full browser test) |
| CM-040 | command | `tools/ui/pw.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/pw.py` (run in round 2: used by every browser tool) |
| CM-041 | command | `tools/ui/test_report.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/test_report.py` (run in round 2: docs/TEST_REPORT.md) |
| CM-042 | command | `tools/ui/walkthrough_shots.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/ui/walkthrough_shots.py` (run in phase 8 (docs/WALKTHROUGH.md)) |
| CM-043 | command | `tools/guide/build.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/build.py` (run in round 2: guide build) |
| CM-044 | command | `tools/guide/ch_appendix.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-045 | command | `tools/guide/ch_cases.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-046 | command | `tools/guide/ch_intro.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-047 | command | `tools/guide/ch_journey.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-048 | command | `tools/guide/ch_rest.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-049 | command | `tools/guide/ch_score.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-050 | command | `tools/guide/ch_stages.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-051 | command | `tools/guide/coverage.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-052 | command | `tools/guide/coverage_check.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/coverage_check.py` (run in round 2: coverage check) |
| CM-053 | command | `tools/guide/docshots.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/docshots.py` (run in round 2: this file) |
| CM-054 | command | `tools/guide/explain.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-055 | command | `tools/guide/facts.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/facts.py` (run in round 2: guide numbers) |
| CM-056 | command | `tools/guide/inv.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/inv.py` (run in round 2: item codes) |
| CM-057 | command | `tools/guide/inventory.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/inventory.py` (run in round 2: inventory) |
| CM-058 | command | `tools/guide/layout.py` | 128 | [commands.png](images/terminal/commands.png) | §11 commands |
| CM-059 | command | `tools/guide/lint_ar.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/lint_ar.py` (run in round 2: writing rules) |
| CM-060 | command | `tools/guide/model.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/model.py` (run in round 2: guide content model) |
| CM-061 | command | `tools/guide/render_docx.py` | 128 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/render_docx.py` (run in round 2: Word) |
| CM-062 | command | `tools/guide/render_html.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/render_html.py` (run in round 2: PDF) |
| CM-063 | command | `tools/guide/shots.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `tools/guide/shots.py` (run in round 2: guide screenshots) |
| CM-064 | command | `ido_talent_ai/ido_talent_ai/scripts/seed_demo.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `ido_talent_ai/ido_talent_ai/scripts/seed_demo.py` (run in round 2: demo setup and test users) |
| CM-065 | command | `ido_talent_ai/ido_talent_ai/scripts/submit_demo_applications.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `ido_talent_ai/ido_talent_ai/scripts/submit_demo_applications.py` (run in round 2: 24 applications) |
| CM-066 | command | `talent-engine/eval/bench.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/eval/bench.py` (run in phase 4) |
| CM-067 | command | `talent-engine/eval/make_gold.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/eval/make_gold.py` (run in phase 4) |
| CM-068 | command | `talent-engine/eval/run.py` | 129 | [commands.png](images/terminal/commands.png) | §11 `talent-engine/eval/run.py` (run in phase 4 (docs/EVALUATION_REPORT.md)) |
| CM-069 | command | `bench get-app` | 129 | [commands.png](images/terminal/commands.png) | §11 `bench get-app` (run in phase 7 clean install rehearsal; install-app also by reset_demo.sh in round 2) |
| CM-070 | command | `bench --site <site> install-app ido_talent_ai` | 129 | [commands.png](images/terminal/commands.png) | §11 `bench --site <site> install-app ido_talent_ai` (run in phase 7 clean install rehearsal; install-app also by reset_demo.sh in round 2) |
| CM-071 | command | `bench --site <site> migrate` | 129 | [commands.png](images/terminal/commands.png) | §11 `bench --site <site> migrate` (run in round 2 on talent.localhost and test.localhost) |
| CM-072 | command | `bench --site <site> run-tests --app ido_talent_ai` | 129 | [commands.png](images/terminal/commands.png) | §11 `bench --site <site> run-tests --app ido_talent_ai` (run in round 2 on talent.localhost and test.localhost) |
| CM-073 | command | `bench --site <site> uninstall-app ido_talent_ai` | 129 | [commands.png](images/terminal/commands.png) | §11 `bench --site <site> uninstall-app ido_talent_ai` (run in phase 7 clean install rehearsal; install-app also by reset_demo.sh in round 2) |
| DC-001 | decision | `CLAUDE.md decision 1: Application-form answers are the primary data source.` | 129 | [decisions.png](images/terminal/decisions.png) | §4 C07 (no CV) and C01–C09 |
| DC-002 | decision | `CLAUDE.md decision 2: Weights are percentages that must total 100%.` | 27 | [S01_profile.png](images/fit/S01_profile.png) | §10 Frappe `test_weights_must_total_100_to_approve`; §5 K14 |
| DC-003 | decision | `CLAUDE.md decision 3: Hard eligibility rules` | 81 | [S06_stage_07.png](images/steps/S06_stage_07.png) | §10 Frappe `test_engine_payload_has_no_identity`; §5 K02 |
| DC-004 | decision | `CLAUDE.md decision 4: Redaction happens before any LLM step.` | 88 | [CV_redaction.png](images/steps/CV_redaction.png) | §10 engine redaction tests; §4 C01 |
| DC-005 | decision | `CLAUDE.md decision 5: Every judgement needs evidence` | 45 | [S09c_evidence.png](images/fit/S09c_evidence.png) | §10 engine evidence tests; §5 K04, K05 |
| DC-006 | decision | `CLAUDE.md decision 6: The LLM judges, code computes.` | 28 | [S01b_criteria.png](images/steps/S01b_criteria.png) | §10 engine scoring tests; §8 score example |
| DC-007 | decision | `CLAUDE.md decision 7: AI never changes an applicant's status.` | 43 | [S09_head.png](images/steps/S09_head.png) | §10 Frappe `test_result_sets_ai_fields_but_never_the_status`; §3 R03 |
| DC-008 | decision | `CLAUDE.md decision 8: AI provider is configurable (local \| cloud)` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §10 engine `test_llm` cloud path |
| DC-009 | decision | `CLAUDE.md decision 9: OCR is an off-the-shelf tool (PaddleOCR), not trained.` | 85 | [CV_scan.png](images/fit/CV_scan.png) | §4 C01, C09 |
| DC-010 | decision | `CLAUDE.md decision 10: Names follow the client's requirements document` | 129 | [decisions.png](images/terminal/decisions.png) | §3 R01–R07 (screen names) |
| DC-011 | decision | `CLAUDE.md decision 11: Scope.` | 59 | [S15_acceptance.png](images/steps/S15_acceptance.png) | §12 postponed features (not built) |
| DC-012 | decision | `CLAUDE.md decision 12: The client's 8 acceptance criteria` | 59 | [S15_acceptance.png](images/steps/S15_acceptance.png) | §12 acceptance criteria |
| DC-013 | decision | `CLAUDE.md decision 13: The engine owns the AI/OCR provider settings` | 56 | [S13_settings.png](images/fit/S13_settings.png) | §10 engine settings tests |
| DC-014 | decision | `CLAUDE.md decision 14: An unreadable CV never fails a screening` | 129 | [decisions.png](images/terminal/decisions.png) | §4 C08; §1 F1 |
| DC-015 | decision | `CLAUDE.md decision 15: Time` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §10 Frappe `test_engine_payload_has_no_identity` (UTC) |
| DC-016 | decision | `CLAUDE.md decision 16: Web form` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §4 C01–C09 (our form) |
| DC-017 | decision | `PROGRESS.md (Phase 5 (continued) — CV analysis in…): Redaction keeps line breaks` | 88 | [CV_redaction.png](images/steps/CV_redaction.png) | §12 decisions taken alone |
| DC-018 | decision | `PROGRESS.md (Phase 5 (continued) — CV analysis in…): Layout in display pixels` | 86 | [CV_pdf.png](images/fit/CV_pdf.png) | §12 decisions taken alone |
| DC-019 | decision | `PROGRESS.md (Phase 8 — talent pool (feature 13)…): Embeddings on CPU in a separate service` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §12 decisions taken alone |
| DC-020 | decision | `PROGRESS.md (Phase 8 — talent pool (feature 13)…): What is embedded` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §12 decisions taken alone |
| DC-021 | decision | `PROGRESS.md (Phase 8 — talent pool (feature 13)…): One suggestion per person` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §12 decisions taken alone |
| DC-022 | decision | `PROGRESS.md (Phase 8 — talent pool (feature 13)…): Suggestions are filtered to the host's own applicants` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §12 decisions taken alone |
| DC-023 | decision | `PROGRESS.md (Phase 8 — talent pool (feature 13)…): Old-application demo case` | 129 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-024 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): No change to HRMS templates` | 32 | [S03_jobs.png](images/steps/S03_jobs.png) | §12 decisions taken alone |
| DC-025 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): Fonts bundled in the app` | 129 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-026 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): English stage notes are stored next to the Arabic ones` | 129 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-027 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): Synthetic Employee records for the demo users` | 129 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-028 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): A CV problem never fails a screening` | 129 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-029 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): "إعادة تقييم الكل" skips applicants without consent` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-030 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): Screenshots cut to the part the page explains` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-031 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): Page numbers read from the printed PDF` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-032 | decision | `PROGRESS.md (Round 2 — completion, design pass, full…): The Word file is checked through LibreOffice` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-033 | decision | `PROGRESS.md (Round 3 — consent defaults…): Frappe's copy of the AI result goes too` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-034 | decision | `PROGRESS.md (Round 3 — consent defaults…): A withdrawal is final for that application` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-035 | decision | `PROGRESS.md (Round 3 — consent defaults…): The engine keeps the reference only` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-036 | decision | `PROGRESS.md (Round 3 — consent defaults…): The earliest later copy becomes the original` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-037 | decision | `PROGRESS.md (Round 3 — consent defaults…): A paper consent carries the current consent text version` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-038 | decision | `PROGRESS.md (Round 3 — consent defaults…): Score 0 means no score in the list` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-039 | decision | `PROGRESS.md (Round 4 — Nadine's review of the guide…): PDF text is rebuilt from characters, not spans` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-040 | decision | `PROGRESS.md (Round 4 — Nadine's review of the guide…): A weak OCR line is removed, not down-weighted` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-041 | decision | `PROGRESS.md (Round 4 — Nadine's review of the guide…): The leak guard is a second gate` | 130 | [decisions.png](images/terminal/decisions.png) | §12 decisions taken alone |
| DC-042 | decision | `OPEN_QUESTIONS #1: Production HRMS commit on the `develop` branch (the demo runs 17.0.0-dev). Our dev bench p` | 130 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 1 |
| DC-043 | decision | `OPEN_QUESTIONS #2: Background **workers** on the production site: `frappe.enqueue` (queue `long`) needs RQ wo` | 130 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 2 |
| DC-044 | decision | `OPEN_QUESTIONS #3: How much GPU memory does the Luna stack (`remote-sdk`, `video-agent`, user awais) need whe` | 130 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 3 |
| DC-045 | decision | `OPEN_QUESTIONS #4: Where is this GPU server physically (inside KSA or not)? Decides whether real CVs may ever` | 130 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 4 |
| DC-046 | decision | `OPEN_QUESTIONS #6: Exact hard-rule values per role (nationality, height, weight, age range) and whether they ` | 130 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 6 |
| DC-047 | decision | `OPEN_QUESTIONS #7: Consent text (Arabic) for the application form, and the retention period for applicants' d` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 7 |
| DC-048 | decision | `OPEN_QUESTIONS #8: Dedicated API user / key on the client site for the engine callback, with minimum permissi` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 8 |
| DC-049 | decision | `OPEN_QUESTIONS #9: Production time zone (demo runs Africa/Cairo; our dev site uses Asia/Riyadh)` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 9 |
| DC-050 | decision | `OPEN_QUESTIONS #13: The phase-4 accuracy (98% exact levels) is measured on **synthetic** applicants. Real accu` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 13 |
| DC-051 | decision | `OPEN_QUESTIONS #15: MariaDB 11.8 runs with `innodb_snapshot_isolation=ON`: concurrent writers get error 1020 i` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 15 |
| DC-052 | decision | `OPEN_QUESTIONS #16: Public form rate limit: 20 applications per IP per 10 minutes (site config `talent_ai_appl` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 16 |
| DC-053 | decision | `OPEN_QUESTIONS #17: Arabic for HRMS's own labels: HRMS develop ships `ar.po` with many empty strings. Round 2 ` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 17 |
| DC-054 | decision | `OPEN_QUESTIONS #18: The demo's form also has "الصورة الشخصية" and "الشهادات". Not built: the requirement list ` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 18 |
| DC-055 | decision | `OPEN_QUESTIONS #20: Applications entered by HR in the desk (paper forms) have no consent record. **Default in ` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 20 |
| DC-056 | decision | `OPEN_QUESTIONS #21: What happens to an applicant who withdraws consent? **Default in force until the client co` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question 21 |
| DC-057 | decision | `OPEN_QUESTIONS #A1: What happens with a corrupt or unreadable CV?` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A1 |
| DC-058 | decision | `OPEN_QUESTIONS #A2: Does a client-specific web form (`job-application-ksa`) exist?` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A2 |
| DC-059 | decision | `OPEN_QUESTIONS #A3: Separate console port?` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A3 |
| DC-060 | decision | `OPEN_QUESTIONS #A4: Who owns the AI/OCR provider settings?` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A4 |
| DC-061 | decision | `OPEN_QUESTIONS #A5: Is the national ID sent to the engine?` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A5 |
| DC-062 | decision | `OPEN_QUESTIONS #A6: Time zones` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A6 |
| DC-063 | decision | `OPEN_QUESTIONS #A7: GPU cap and ports` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A7 |
| DC-064 | decision | `OPEN_QUESTIONS #Q5: CV upload for Guests on the application form` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q5 |
| DC-065 | decision | `OPEN_QUESTIONS #Q10: RQ worker overhead` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q10 |
| DC-066 | decision | `OPEN_QUESTIONS #Q11: OCR confidence threshold` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q11 |
| DC-067 | decision | `OPEN_QUESTIONS #Q12: Judge quality of Qwen3-8B-AWQ` | 131 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q12 |
| DC-068 | decision | `OPEN_QUESTIONS #Q14: Commit the dev bench scripts?` | 132 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q14 |
| DC-069 | decision | `OPEN_QUESTIONS #Q19: Enforce a reason for every status change?` | 132 | [open_questions.png](images/terminal/open_questions.png) | §12 open question Q19 |
| DC-070 | decision | `OPEN_QUESTIONS #A8: Which Docker builder may we use?` | 132 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A8 |
| DC-071 | decision | `OPEN_QUESTIONS #A9: Frappe MariaDB in memory?` | 132 | [open_questions.png](images/terminal/open_questions.png) | §12 open question A9 |
| EV-001 | evaluation | `gold-set run 8B v1` | 9 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-002 | evaluation | `gold-set run 8B v2` | 132 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-003 | evaluation | `gold-set run 4B v1` | 132 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-004 | evaluation | `throughput with 2 workers (13.4 min per 100)` | 132 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-005 | evaluation | `throughput with 4 workers (7.8 min per 100)` | 9 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-006 | evaluation | `throughput with 8 workers (5.4 min per 100)` | 9 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-007 | evaluation | `evaluation: rerun` | 9 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-008 | evaluation | `evaluation: name-swap` | 9 | [evaluation.png](images/terminal/evaluation.png) | §13 evaluation results |
| EV-009 | evaluation | `evaluation: ocr-threshold` | 85 | [CV_scan.png](images/fit/CV_scan.png) | §13 evaluation results |
| EV-010 | evaluation | `evaluation: quote-ratio` | 80 | [S06_stage_06.png](images/steps/S06_stage_06.png) | §13 evaluation results |
| SY-001 | security | `engine → Frappe results signed with HMAC-SHA256 (timestamp + body)` | 10 | [diagram.png](images/diagram.png) | §10 Frappe `test_callback_signature` |
| SY-002 | security | `Bearer API key per tenant on every /v1 call; key never in browser code` | 73 | [C_dev.png](images/fit/C_dev.png) | §10 engine auth tests |
| SY-003 | security | `console login with a signed HttpOnly cookie (12 h)` | 60 | [card_C_login.png](images/fit/card_C_login.png) | §10 engine `test_console` |
| SY-004 | security | `ports bound to 127.0.0.1 and the Tailscale address only; DB/Redis on 127.0.0.1` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §11 `make ps` |
| SY-005 | security | `redaction before any LLM step (name, phone, e-mail, ID, dob, nationality, gender, address)` | 78 | [S06_stage_04.png](images/steps/S06_stage_04.png) | §10 engine redaction tests |
| SY-006 | security | `raw national ID never leaves Frappe: id_token = HMAC-SHA256(national_id, secret)` | 10 | [diagram.png](images/diagram.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SY-007 | security | `AI fields and identity at permission level 1 (HR roles only)` | 11 | [diagram.png](images/diagram.png) | §10 Frappe `test_ai_fields_are_hr_only`; §3 R06 |
| SY-008 | security | `every HR method refuses other users first (permanent test)` | 11 | [diagram.png](images/diagram.png) | §10 Frappe `test_every_hr_method_refuses_other_users_first` |
| SY-009 | security | `public form rate limit per IP` | 34 | [S05_form_1.png](images/steps/S05_form_1.png) | §10 Frappe `test_application_is_always_saved` |
| SY-010 | security | `CV size limit 10 MB and allowed extensions` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §4 C08 |
| SY-011 | security | `consent recorded with its version; withdrawal stops processing and deletes the pool profile` | 36 | [S05_form_3.png](images/steps/S05_form_3.png) | §10 Frappe `test_withdrawn_consent_stops_processing` |
| SY-012 | security | `retention period for the talent pool` | 53 | [S11_pool.png](images/fit/S11_pool.png) | §5 K12 |
| SY-013 | security | `every AI action and HR decision in the audit log (with reason and actor)` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §5 K09 |
| SY-014 | security | `secrets in Password fields and .env files, never in git, logs, the guide or images` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §3 R07 |
| SY-015 | security | `no third-party calls from the screens (fonts served locally)` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §10 engine `test_fonts_are_served_locally` |
| SY-016 | security | `console static files: path traversal refused` | 73 | [C_dev.png](images/fit/C_dev.png) | §10 engine `test_static_path_traversal_blocked` |
| SY-017 | security | `every applicant text escaped before display` | 109 | [CV_redaction.png](images/fit/CV_redaction.png) | §5 K13 |
| SY-018 | security | `the LLM never sees nationality, gender, age, name, photo or IDs` | 10 | [diagram.png](images/diagram.png) | §10 Frappe `test_engine_payload_has_no_identity` |
| SY-019 | security | `deleting an applicant de-identifies the audit rows` | 57 | [S14_audit.png](images/steps/S14_audit.png) | §10 Frappe test suite |
| AR-001 | architecture | `engine service db (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-002 | architecture | `engine service redis (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-003 | architecture | `engine service api (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-004 | architecture | `engine service worker (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-005 | architecture | `engine service vllm (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-006 | architecture | `engine service embed (compose project talentai)` | 10 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-007 | architecture | `dev bench service mariadb (compose project talentai-frappe)` | 132 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-008 | architecture | `dev bench service redis-cache (compose project talentai-frappe)` | 132 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-009 | architecture | `dev bench service redis-queue (compose project talentai-frappe)` | 132 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-010 | architecture | `dev bench service bench (compose project talentai-frappe)` | 132 | [diagram.png](images/diagram.png) | §11 `make ps` |
| AR-011 | architecture | `repository talent-ai (workspace, docs, engine, dev bench scripts)` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-012 | architecture | `repository ido_talent_ai (Frappe app, bench get-app)` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-013 | architecture | `install on the platform: bench get-app → install-app → migrate → settings` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-014 | architecture | `uninstall leaves the platform as it was (custom fields and permission rows removed)` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-015 | architecture | `the engine is standalone; Frappe is the first adapter (HTTP + HMAC callback)` | 10 | [diagram.png](images/diagram.png) | §11 commands |
| AR-016 | architecture | `one tenant per host system (API key)` | 10 | [diagram.png](images/diagram.png) | §11 commands |
| AR-017 | architecture | `vLLM capped at 40% of the shared GPU` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-018 | architecture | `the dev Frappe database runs in memory, for testing only` | 132 | [diagram.png](images/diagram.png) | §11 commands |
| AR-019 | architecture | `Docker images built with the default builder only` | 132 | [diagram.png](images/diagram.png) | §11 commands |
