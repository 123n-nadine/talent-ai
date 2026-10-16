# Testing

Three levels: (1) Nadine runs the full cycle by hand, (2) the client's acceptance criteria, (3) automated tests and model evaluation. All data is synthetic.

## 1. Full cycle by hand (Talent Console first, then local Frappe)

Run this list in order. Each line has an expected result. Note anything different.

| # | Do | Expect |
|---|---|---|
| 1 | Create job profile "مشرف أمن" from the template; set weights 30/20/15/15/8/7/5 | Total chip shows 100%; approve enabled |
| 2 | Change one weight so the total is 105 | Approve blocked (UI and API both refuse) |
| 3 | Press «اقتراح معايير AI» on a new job title | Draft appears; nothing is used until approved |
| 4 | Approve the profile | Version 1 recorded with approver and time |
| 5 | Submit an application with all answers, no CV | Saved immediately; Processing → Completed; every level cites a form answer |
| 6 | Submit one with some answers blank and one answer `0` | Blank shows «لم يُجب» + missing evidence; `0` treated as a real answer; coverage lower; Needs Review if < 60% |
| 7 | Submit one with a text PDF CV | CV text extracted; levels show «تؤكده السيرة» where relevant |
| 8 | Submit one with a scanned Arabic CV (image) | OCR used, confidence shown; redacted text has no name/phone/ID |
| 9 | Submit one with a corrupt file | Application saved; assessed from answers only with flag «ملف السيرة غير مقروء» (`cv_unreadable`) shown clearly; status Completed or Needs Review by the usual rules, never Failed |
| 10 | Height 172 declared | «غير مستوفٍ حسب التصريح»; not ranked; not rejected; status unchanged |
| 11 | Height left blank | «يحتاج مراجعة» |
| 12 | Answer says 6 years, CV says 2 | Contradiction flag; lower value used; Needs Review |
| 13 | Same applicant applies twice | Duplicate linked; only one ranked; nothing deleted |
| 14 | Open the ranking | Only completed + eligible + current; other groups collapsed with reasons; order matches scores |
| 15 | Override one level with a reason | Score recomputes; «تعديل HR» tag; audit entry with user and reason |
| 16 | Try override without a reason | Refused |
| 17 | Edit an applicant's answer after evaluation | Result flagged «لا تعكس آخر تعديل»; leaves ranking until rescreen |
| 18 | Approve a new profile version (change a weight) | Old results stale; «إعادة تقييم الكل» rescreens; ranking updates |
| 19 | Stop the engine (or LLM) and submit an application | Application still saved; AI status Failed/Processing; retry works when service is back |
| 20 | Shortlist / Hold / Reject as HR | Status changes only through these buttons; reason and user saved |
| 21 | Check that the AI never changed any status | Audit log shows status changes only by users |
| 22 | Export ranking CSV | Opens correctly in Excel with Arabic (UTF-8 BOM) |
| 23 | Switch AR/EN | Arabic screens RTL and correct; English LTR |
| 24 | Delete a candidate via API | Documents, profile, vectors, results gone in the engine, and the stored CV file too |
| 25 | Enter a paper application in the desk (Job Applicant, no consent box) on an AI opening (OPEN_QUESTIONS #20, default) | Saved; AI status «بانتظار الموافقة»; nothing sent to the engine; listed in the ranking group «بانتظار الموافقة» |
| 26 | «تسجيل الموافقة» on it: first with an empty source, then «ورقة موقّعة» | Empty source refused; then «سجّل الموافقة» = you, «مصدر الموافقة», the time and an audit row; the screening starts by itself |
| 27 | «سحب موافقة المعالجة» on a ranked applicant, with a reason (OPEN_QUESTIONS #21, default) | Out of the ranking at once, in «مستبعد: سحب الموافقة» with no score; no AI section left; in the engine `GET /v1/candidates/{ref}` shows no facts, documents or screenings and the CV file is gone; the application itself stays |

## 2. Client acceptance criteria (definition of done, phase 1)

From the client's requirements document §8, in its words with how we prove each one.

| # | Criterion (client) | How we prove it |
|---|---|---|
| 1 | عند تقديم طلب من Web Form، يظهر Job Applicant مرتبطًا بالوظيفة وبجميع الإجابات | Submit on local site; Job Applicant has job_title link and every answer row; screenshot |
| 2 | عند تفعيل AI، تظهر حالة Processing ثم Completed أو Needs Review أو Failed بوضوح | Cases 5, 6, 9 and 19 above (Failed comes from case 19, engine down); screenshots of each status |
| 3 | كل درجة لها سبب ودليل من بيانات المتقدم، ولا تظهر مهارات لم يذكرها | Automated: 100% of levels > 0 have evidence that matches a stored answer or a literal quote; gold-set report |
| 4 | عند تعديل بيانات المتقدم، لا تبقى النتيجة القديمة وكأنها حديثة | Case 17 |
| 5 | قائمة المرشحين لا تخلط بين الوظائف، وقرار التوظيف لا يتغير دون مستخدم مخوّل | Two jobs with applicants; ranking per job; permission test with a non-HR user; case 21 |
| 6 | عند تعطل خدمة AI، يظل تقديم الطلب يعمل بشكل طبيعي | Case 19 |
| 7 | المقابلات والاختبارات والعروض تستخدم بيانات المرشح نفسه | Out of phase 1 scope (those features are postponed). Mark "not applicable in phase 1" |
| 8 | تظهر الشاشات العربية بشكل صحيح، مع احترام صلاحيات كل مستخدم | Screenshots of each screen in Arabic; role tests (HR Manager, HR User, Employee) |

Record results in `docs/ACCEPTANCE_REPORT.md` with date, build commit and evidence.

## 3. Automated tests and evaluation

**Unit (pytest, engine):** scoring examples (81.5 and 89), bands at 49.9/50/74.9/75, mandatory rule, coverage and needs-review threshold, eligibility outcomes, Arabic reason text, blank vs 0, evidence matcher (Arabic normalisation: أ/إ/آ→ا, ة/ه, ى/ي, Arabic-Indic digits), redaction recognisers, HMAC sign/verify, weights validation, stale and duplicate logic, ranking groups.

**Integration:** full pipeline with the fake LLM in CI; with the real local LLM as a marked slow test.

**Frappe app tests:** after_insert enqueue, callback signature, writing results, stale on update, permissions, engine-down behaviour.

**Model evaluation (gold set):**

| metric | target |
|---|---|
| levels > 0 with evidence | 100% |
| CV quotes found in text | 100% (others dropped automatically) |
| extraction accuracy (years, licence, certifications) | ≥ 90% |
| eligibility correct | 100% (code rules) |
| agreement with hand labels (exact level / within one step) | report; target set after first run |
| same result on rerun | 100% |
| name-swap invariance | 100% same levels |
| time per application, per 1000 on this server | report |

Do not invent accuracy or speed numbers in any document; write "measured in evaluation" until there is a report.
