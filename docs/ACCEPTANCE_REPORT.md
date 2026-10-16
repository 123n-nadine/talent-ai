# Acceptance report — the client's 8 criteria (phase 1)

Written for: Nadine, Abdullah and the client's HR/IT reviewers.

Where: the local Frappe bench (`dev-frappe/`, Frappe v16.31.0, ERPNext v16.32.0, HRMS develop 640af1592a01) with the app `ido_talent_ai` and the engine `talent-engine` (Qwen3-8B-AWQ on the shared GPU, PaddleOCR on CPU). Data: the opening «مشرف أمن — الرياض» with 25 synthetic applicants submitted through the public form, plus test applications created during the run. **Synthetic data only.**

How: `tools/ui/acceptance.py` drives a real Chrome (headless) as the real users — a Guest on the public form, `hr.manager@example.com`, `hr.user@example.com` and `employee@example.com` (Employee role only) — and checks the database and the engine through the same APIs the screens use. Run on 2026-10-16. Result: **13 of 13 checks passed** (`docs/screenshots/acceptance/acceptance.json`). The automated Frappe tests (11) and engine tests (109) also pass.

| # | Criterion (client's words) | Result | Evidence |
|---|---|---|---|
| A1 | عند تقديم طلب من Web Form، يظهر Job Applicant مرتبطًا بالوظيفة وبجميع الإجابات | ✅ | A Guest filled `/ai-apply/new` with a PDF CV: the Job Applicant was saved in 0.5 s, linked to HR-OPN-2026-0001, with **11 of 11** answers in «إجابات الفرز» and the CV attached. Blank stays «لم يُجب», 0 stays 0 (Frappe test `test_application_saved_with_all_answers_even_if_engine_down`). Screens: `A1_form_filled.png`, `A1_form_thanks.png` |
| A2 | عند تفعيل AI، تظهر حالة Processing ثم Completed أو Needs Review أو Failed بوضوح | ✅ | On the open applicant form the status went **Processing → Completed** in 43 s **without reloading the page** (realtime). Needs Review: 2012 (answer vs CV contradiction) and 2021 (mandatory answer blank). Failed: see A6. Screens: `A2_processing.png`, `A2_completed.png` |
| A3 | كل درجة لها سبب ودليل من بيانات المتقدم، ولا تظهر مهارات لم يذكرها | ✅ | Across all 26 screenings of the opening, **145 of 145** levels above 0 carry verified evidence: a form answer equal to the stored answer, or a CV quote that exists in the redacted CV text. Quotes that are not in the text are dropped (flag «اقتباس غير موجود») and missing evidence is level 0 with «دليل ناقص», never a guess. Durations in CV quotes are levelled in code. On the 50-applicant gold set: 100% evidence, 98% exact levels (`EVALUATION_REPORT.md`) |
| A4 | عند تعديل بيانات المتقدم، لا تبقى النتيجة القديمة وكأنها حديثة | ✅ | HR changed one answer of 2004 after evaluation → banner «النتيجة لا تعكس آخر تعديل», the result moved to the «قديم» group and out of the ranking; «إعادة التقييم» brought it back (new score 78, ranked again). A new profile version (v2) marked all 26 results stale until «إعادة تقييم الكل» (125 s). Screens: `A4_stale_banner_ai.png`, `G1_ranking_stale_after_v2.png`, `G7_batch_rescoring.png` |
| A5 | قائمة المرشحين لا تخلط بين الوظائف، وقرار التوظيف لا يتغير دون مستخدم مخوّل | ✅ | Two openings (Riyadh, Jeddah) ranked separately with **no overlap**; comparison refuses applicants of two openings. The AI never writes `status`: after the run the only status change was the one HR decision, made with a reason and logged with the user. A decision without a reason is refused. The Employee user gets **403** on the ranking, on decisions and on reading a Job Applicant. Screens: `A5_ranking_jeddah.png`, `A5_decision_ai.png`, `A8_employee_denied.png` |
| A6 | عند تعطل خدمة AI، يظل تقديم الطلب يعمل بشكل طبيعي | ✅ | The engine API container was stopped. A Guest application was still saved in 0.5 s; the AI job retried 3 times and ended **Failed** with «تعذّر الوصول إلى محرك الذكاء» while the application stayed visible with all answers. After starting the engine, «إعادة المحاولة» → **Completed**. Screens: `A6_form_engine_down_thanks.png`, `A6_failed_ai.png`, `A6_after_retry_ai.png` |
| A7 | المقابلات والاختبارات والعروض تستخدم بيانات المرشح نفسه | n/a | Interviews, technical tests and offers are **postponed** features (decision 11) and were not built. HRMS's own Interview / Job Offer screens keep using the same Job Applicant record; the app does not touch them |
| A8 | تظهر الشاشات العربية بشكل صحيح، مع احترام صلاحيات كل مستخدم | ✅ | Every Talent AI screen renders in Arabic RTL with no JavaScript errors (HR Manager and HR User). The AI section is at permission level 1: HR Manager / HR User see it, other roles cannot open Job Applicant at all. Screens: `A8_hr_user_ai.png`, `A8_employee_denied.png`, and all screens in `docs/screenshots/` |

## The guide's continuation steps checked in the same run

| Step | Result | Evidence |
|---|---|---|
| 1+ weights total 100% enforced, impact preview, versions | ✅ | Weights at 105% → «اعتماد» refused by the server. At 100% the impact preview listed 26 applicants (15 scores and 6 ranks move); approval created **v2** and made 26 results stale | `G1_weights_105.png` |
| 7 batch monitor with real counts | ✅ | Re-scoring 26 applicants after v2, counts from Job Applicant and AI Recruitment Job | `G7_batch_rescoring.png` |
| 10+ CSV for Excel | ✅ | UTF-8 with BOM, Arabic header «الترتيب، المتقدم، الاسم، الدرجة…» | `acceptance.json` |
| 10c comparison (feature 10) | ✅ | 3 applicants criterion by criterion with their evidence; mixed openings refused | `G10c_compare.png` |
| 13 settings live in the engine | ✅ | «عدد المحاولات» changed in Frappe → read back from `GET /v1/settings`, then restored | `G13_settings.png` |
| 14 audit log | ✅ | Every job, decision, override, export, profile approval and setting change with user and reason | `G14_audit_log.png` |

## Clean install on a fresh site

`dev-frappe/clean_install.sh` (log: `docs/screenshots/acceptance/clean_install.log`): a separate bench with the same frappe/erpnext/hrms commits, **`bench get-app` of `ido_talent_ai` from its git repository**, a new site with ERPNext + HRMS, `install-app` (42 custom fields), `migrate`, the app tests (**11 passed**), `uninstall-app` (custom fields 0, permission rows 0, Talent AI DocTypes 0), then a Job Applicant created on the same site without the app. Deployment steps: `DEPLOY.md`.

## Not covered here (and why)

- **Real applicants.** Accuracy is measured on synthetic data only; the client's HR needs to label 30–40 real applications inside their environment (OPEN_QUESTIONS #13).
- **The client's real site** was not touched (project rule). Production versions, workers, scheduler and network are listed in `DEPLOY.md` as items to confirm.
- **Talent pool (feature 13)** is phase 2 of the client's plan; it is reported in `PROGRESS.md` (phase 8).

## How to run it again

```bash
dev-frappe/reset_demo.sh                       # clean demo (opening + 25 applicants)
talent-engine/.venv/bin/python tools/ui/acceptance.py /tmp/acceptance   # ~20 minutes
dev-frappe/reset_demo.sh                       # the run changes the demo data; reset afterwards
```
