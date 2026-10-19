# Final pre-handover QA — Talent AI

Written for: Nadine and whoever signs the handover. Date 2026-10-19. Everything below was measured on this server (local bench with the client's platform versions, synthetic data only). Branch `p23-final-qa` in both repos; nothing pushed.

## 1. Verdict

**Ready to hand over, with one decision left for Nadine (Q8).**

- Every claim of the management walkthrough checked here holds on the system. Three held only after today's fixes: the free-text redaction (Q1), access to the settings (Q5) and the automatic hourly retry after an engine outage (Q9).
- Nine findings were fixed, each with a regression test: eight in the product (Q1, Q2, Q3, Q5, Q6, Q7, Q7b, Q9) and one in the test harness (Q4).
- One finding needs a decision (Q8): English *scanned* CVs lose OCR-misread tool words to the privacy filter. It removes too much, never too little.
- No accuracy or speed number in the document changed. Only the test counts grew.
- All suites are green on the final code: engine 139 + 1 skipped, Frappe 30, browser 40/40, gold set 0 failures (identical judgement by judgement after the redaction fix).

## 2. Numbers before and after

| What | Document says | Baseline (before fixes) | After fixes |
|---|---|---|---|
| Engine tests | 135 + 1 skipped | 135 passed, 1 skipped (OCR) | **139 passed, 1 skipped** (4 new regression tests); ruff and mypy clean |
| Frappe app tests | 25 | 25 OK | **30 OK** (5 new regression tests) |
| Browser E2E | 40/40 | 38/40 — K09 and K15 failed on a timing race in the test harness, not in the product (see §5); both pass when rerun | **40/40** twice: after the first fixes (32 min) and on the final code (47 min), each from a clean reset |
| Gold set, failures | 0 of 55 | 0 of 55 | 0 of 55 |
| Gold set, exact / within one step | — | 98.8% / 100% | 98.8% / 100% |
| Code-scored judgements | 100% (311) | 100% of 312 | 100% of 312 |
| Model-judged judgements | 65% exact / 94% within one step (17) | 75% / 100% of 16 (the one «licence from the CV» disagreement of 2026-10-18 did not recur) | 75% / 100% of 16 — judgement by judgement identical to the baseline (315 code-levelled + 18 model-judged, 0 changed) |
| Name-swap / rerun | 100% / 100% | name-swap 100% (rerun: 100% on 2026-10-18, not repeated today) | name-swap 100% |
| Time per application (gold set) | avg ~18 s, max ~45 s | mean 17.6 s, median 22.3 s, max 44.3 s | mean 17.9 s, median 22.4 s, max 44.1 s |
| 1,000 applications with 8 workers | ≈ 1 hour | **100-application load test, extrapolated** (the GPU is shared: another user's process was on it, so the full 1,000 run was not done): 100 applicants (62 with a text PDF), 8 workers, 359 s from the last submission to the last result, 16.7 per minute → **≈ 60 min per 1,000**; GPU peak 9.6 GB | not repeated (no change to the model or the pipeline cost) |
| National ID outside Frappe | never leaves Frappe | 0 hits for the demo IDs in every text/JSON column of the engine database, in Redis (7 keys) and in the api, worker, vLLM and embed logs | same |

Raw reports: `talent-engine/eval/reports/2026-10-19_1052-qa-8b-v1.*` (baseline), `2026-10-19_1125-qa-8b-v1-fixed.*` (after), `2026-10-19_1105-bench-qa-w8.json` (load test); `docs/TEST_REPORT.md` (E2E); `docs/qa/audit_extras.json`, `docs/qa/explore.json` / `explore.md`, `docs/qa/postcheck.json` / `postcheck.md`.

The gold set «after» was run on the engine with Q1, the only fix that changes what the model receives. The later engine fix (Q7b) only changes what happens when the queue cannot take a job; the Frappe fixes (Q3, Q5, Q6, Q9) do not touch scoring. Scoring logic, rubric, weights, prompts and model settings were not changed.

Baseline commits: talent-ai `b2b24c9`, ido_talent_ai `a2c12ed` (both `main`, equal to `origin/main`, clean).

## 3. Document vs system audit

`docs/handover/Talent-AI-Management-Walkthrough.pdf`, 37 pages, 13 sections. «How verified» cites the browser E2E case (TEST_REPORT.md, run twice today), the automated test, the rehearsal screens (`demo/screens/`), or a live check of today (`tools/qa/audit_extras.py`, `tools/qa/explore.py`).

| page | claim | how verified | result |
|---|---|---|---|
| 1–2 | Built and tried end to end on a copy with the client's platform versions (Frappe 16.31.0, ERPNext 16.32.0, HRMS develop pinned) | `dev-frappe/VERSIONS.md`; the whole suite below runs on that bench | PASS |
| 2 | 7 of 8 acceptance criteria passed, the 8th (interviews/tests/offers) postponed by agreement | `docs/ACCEPTANCE_REPORT.md`; E2E cases A1–A6, A8 | PASS |
| 2 | 40/40 browser checks | E2E today: baseline 38/40 (two harness races, see §5), then 40/40 twice after the fixes, each from a clean reset | PASS |
| 2, 33 | 0 of 55 failed in the evaluation | gold set today, twice | PASS |
| 2, 33 | 100% of judgements have evidence from the answers or the CV | gold set `levels_gt0_with_evidence` 100% | PASS |
| 2, 33 | ≈ 1 hour for 1,000 applications with 8 workers | 100-application load test today → 60 min extrapolated (54 min on 2026-10-15) | PASS (extrapolated; GPU shared) |
| 2, 32 | 9 kinds of user tried by real login | E2E R01–R09 (9 users × 16 screens + API) | PASS |
| 2 | 136-page guide, rehearsal of the presentation | `docs/guide/talent-ai-full-guide.pdf` 136 pages; `demo/STEPS.md` 16 steps | PASS |
| 3 | The 7-step flow: criteria file → opening → publish → apply → processing → ranking → decision | rehearsal steps 01–13 in a real browser (`tools/demo/rehearsal.py`, screens 01–13) | PASS |
| 4 | If the engine stops, applications are saved and assessed on retry | E2E K15; rehearsal 15a/15b | PASS |
| 4, 11, 32 | The national ID never leaves Frappe (only an HMAC token) | Frappe test `test_engine_payload_has_no_identity`; live search of the engine DB, Redis and logs: 0 hits | PASS |
| 5 | Home page with real counters and the 9 cycle buttons; a button the role may not use is grey | live: `home_counts` = database count; E2E R08; screens 01/02 | PASS |
| 5 | Cycle map with numbers from the site | guide step 0b (`S00_cycle_map`) | PASS |
| 6 | Criteria file: 7 criteria, weights total 100%, five written levels, mandatory → band «low» at level 0, versions with approver and time | E2E K14 (version 2 approved, re-scored); engine tests `test_scoring`; rehearsal screen 02 | PASS |
| 6, 7 | AI-drafted criteria are only a flagged draft, never used before approval; templates by designation | screen 17 (`17_ai_draft_criteria.png`: orange banner, «مسودة», draft flag); engine `normalise_draft` tests; Frappe test for the template copy | PASS |
| 8 | Impact preview before approval; old results marked stale after approval | E2E K14 (`K14_impact_preview.png`, `K14_ranking_stale.png`) | PASS |
| 9 | Weights must total 100%: 105% refused from the screen and the API | E2E K14 (`K14_weights_105.png`); Frappe test `test_weights_must_total_100_to_approve`; live API today: approve refused, status stays Draft | PASS |
| 9 | AI screening per opening: no evaluation unless the profile is approved; can be switched off per opening | Frappe test «AI section on the opening», `opening_ai()` guard; E2E K03 | PASS |
| 10 | Public jobs page and job page with the eligibility requirements and «قدّم الآن» | rehearsal screen 03; E2E C01 form load | PASS |
| 11 | Form in Arabic and English; the ID note («لا يُعرض ولا يُرسل…») | live today: sentence present; English labels present after one click (screen 16) | PASS |
| 12 | 11 screening questions with the zero/blank hint; CV optional; consent mandatory and versioned | live today: 11 `.field.q`, consent `required`; E2E K04 (blank vs 0); Frappe test `test_missing_required_answer_and_consent_are_refused` | PASS |
| 13 | Mobile: one column, nothing cut (375/390 px) | live today at 390 px: no horizontal overflow; design audit 0 issues on the public pages | PASS |
| 14 | Thanks page in < 0.5 s, no score shown, no automatic decision | E2E C01–C09 submit 0.15–0.9 s; rehearsal screen 05 (no score on the page) | PASS |
| 15 | «جاري المعالجة…» refreshes alone; text CV seconds, scanned 35–40 s; 10 stages with result and time | rehearsal screen 06 (processing), 07 (result after 34 s); E2E C02 text PDF 33 s, C01 scan 51.7 s (TEST_REPORT); the document's 35–40 s is the typical value, today's run gave 34 s and 41 s, the E2E scan 51.7 s | PASS (range noted) |
| 16 | CV analysis: boxes by confidence; a weak line is never evidence; all weak → needs review | engine `test_weak_ocr_lines_are_never_evidence`; rehearsal screen 07 (one weak line struck out); E2E C09 bad scan → needs review | PASS |
| 17 | Name, phone, e-mail, ID, DOB, nationality, gender, address removed before the model; name-swap 100% | engine `test_no_personal_data_in_any_model_payload` (every model request body inspected) — **the free-text answer was the gap, fixed today**; `leak_check` 0 on all 220+ stored documents; name-swap 100% today | PASS after fix |
| 18 | Batch screen: counts, average time, failed retried up to 3 times | E2E K14 (`K14_batch_rescoring.png`); K15 three attempts | PASS |
| 19 | Applicant list with AI columns; assessment screen «قراءة فقط — لا يغيّر حالة الطلب» with eligibility, score/band, coverage, rank, summary | live today: labels present on a completed applicant; status untouched | PASS |
| 20 | Strengths / gaps / what raises the score; evidence per criterion; override with a reason, logged; no skill the applicant did not state | E2E K08 (override without reason refused, with reason logged); engine `test_invented_quote_is_dropped_never_guessed`; screen 08 | PASS |
| 21 | Ranking with the approved weights; groups outside the ranking with reasons | E2E K01, K02; screen 09 | PASS |
| 22 | Compare 2–3 applicants; CSV export opens in Excel in Arabic | E2E K11, K10 (BOM + UTF-8) ; screen 10 | PASS |
| 23 | Decision only by HR with a reason; audit log entries | E2E K09 (empty reason refused; who/when logged); screens 11–13; Frappe test `test_hr_decision_needs_a_reason_and_is_logged` | PASS |
| 23 | Audit log records CV opened, compared, pool search, consent, decisions | screen 13 (`cv.viewed`, `ranking.compared`, `hr.decision`, `applicant.consent_recorded`); E2E K12/K16/K17 | PASS |
| 24 | Talent pool: rules first, then similarity; withdrawn consent and expired retention excluded | E2E K12 (20 suggested, 9 excluded incl. consent_withdrawn, retention_expired) | PASS |
| 24 | AI jobs screen with attempts and retry | E2E K15; guide step 12 | PASS |
| 25 | Settings: secrets hidden, kill switch, only HR Manager and System Manager | E2E R04, R07; live today: HR User refused on the page; **the API behind the page answered an HR User (Q5, fixed today)**; after the fix: refused on both; no key in the settings answer (`callback_secret_set` is a boolean) | PASS after fix |
| 26 | Engine down while applying: «الطلب بيتحفظ فوراً، والتقييم بيتعاد لوحده أو بزرار إعادة المحاولة» | E2E K15 (saved, Failed, retry → Completed); code review of the hourly retry + Frappe test: **«by itself» did not happen** (Q9), fixed today | PASS after fix |
| 26–31 | Special cases table | corrupt CV C08; engine down K15; blank/zero K04; contradiction K05; duplicate K06; stale K07; not eligible K02; paper consent K16; withdrawal K17; weak/partial scan screen 18 + engine `test_partial_cv_read_is_flagged_for_hr` | PASS |
| 30 | Engine down: saved in 0.1 s, three attempts, retry in seconds | E2E K15 today: saved 0.17 s, Failed after 25.3 s, retry → Completed in 9.0 s | PASS |
| 32 | 9 roles: UI, direct URL and API | E2E R01–R09 (screens, DENY on URLs, API 403 for non-HR) | PASS |
| 32 | Privacy: local model, no data to an outside service; consent versioned; keys only in config files | engine settings `ai_provider=local`, vLLM on the compose network; secret scan of the repos 0 problems; K16/K17 | PASS |
| 33 | Acceptance table and the accuracy/speed table | numbers in §2 of this report; the free-text accuracy rests on 5 distinct texts (as the document says) | PASS |
| 34–35 | Console; API docs; two private repos; Docker; guide 136 pages; inventory 588 | E2E N01/N02; `/docs` now follows a setting (off in production); `docs/guide/COVERAGE.md` 588 items MISSING 0 | PASS |
| 36–37 | Integration steps and open questions | documentation only (`OPEN_QUESTIONS.md` #22, #23 included) | n/a |

## 4. Exploratory testing beyond the document

Script `tools/qa/explore.py` (results `docs/qa/explore.md`), follow-ups after the fixes `tools/qa/postcheck.py` (`docs/qa/postcheck.md`). All with synthetic applicants on the demo site, which was reset afterwards.

| area | case | result | verdict |
|---|---|---|---|
| file | 0-byte CV | before: saved silently as «no CV» (the applicant never knew). After Q6: refused in the form and by the endpoint with «ملف السيرة فارغ — ارفع الملف الصحيح أو اتركه بدون سيرة», nothing saved | PASS after fix |
| file | wrong type (.exe) | refused at submission: «نوع ملف السيرة غير مدعوم» | PASS |
| file | 11 MB file | refused at submission: «حجم ملف السيرة أكبر من 10 ميجابايت» | PASS |
| file | password-protected PDF | saved, flag `cv_unreadable`, assessed from the answers in 10.5 s | PASS |
| file | 3-page PDF | Completed in 33 s; `pdf_text`, **3 pages**, 1,650 characters (the first run read the details under the wrong key) | PASS |
| file | DOCX | Completed in 39 s | PASS |
| file | scan turned 90° | Needs Review with `low_ocr_confidence` in 41 s (OCR does not turn the page; HR is told, nothing crashes) | PASS (limit noted) |
| file | low-quality photo | Needs Review with `low_ocr_confidence` in 44 s | PASS |
| file | fully English scanned CV | Completed in 44 s. OCR language report: `ocr:paddle_cpu`, confidence 0.98, 1 page, 321 characters; 70% of the letters Latin, the Arabic letters are only the redaction markers. **But** the OCR misread «Power BI» as «Power Bl» and «KPIs» as «KPls», and the English name detector then removed both as person names (Q8, not fixed — §6). The same CV as a text PDF keeps them | PASS (Q8 noted) |
| text | 5,000-character free answer | saved, Completed in 10 s | PASS |
| text | emoji in the name and an answer | saved, Completed | PASS |
| text | mixed Arabic/English | saved, Completed | PASS |
| text | `<script>` and `<img onerror>` in the name and an answer | Frappe's own XSS filter strips the script and the event attribute on save (stored «<img src="x">عمر», «<b>مشرف</b> وردية منذ 2019»); the HR page injects no element and runs no alert | PASS |
| behaviour | double click on «إرسال» | one application (the button is disabled while sending) | PASS |
| behaviour | 20 concurrent submissions, 10 with a CV | 20/20 saved in 0.8 s; all 20 assessed after 132 s; 0 failed | PASS |
| behaviour | restart an engine worker while a scan is processed | assessed 10.5 s after the restart | PASS |
| behaviour | restart the engine's Redis while a scan is processed | before: **the four workers exited** on the lost connection and nothing started them again; every later screening would have waited (Q7). After Q7: the workers came back by themselves 69 s after the restart and the application was assessed. With Redis **stopped** while an application arrives (after Q7b): the engine answered 503, the app tried three times and showed «Failed» in 30 s with the plain sentence, the workers were back as soon as Redis started, and «إعادة المحاولة» gave the result in 12 s; the engine kept three failed screenings and one completed, none left «queued» | PASS after fix |
| behaviour | timeouts | engine down: three attempts then «Failed» in 25 s (E2E K15); a screening with no answer for 30 min is marked Failed by the 2-minute safety net (Frappe test `test_the_safety_nets_read_the_site_clock`) | PASS |
| security | API key in the public page source | absent (no key, no «Bearer») | PASS |
| security | desk pages without login | redirect to login (301) | PASS |
| security | engine console / `/v1` without credentials | console 303 to its login, `/v1/jobs` and `/v1/settings` 401 | PASS |
| security | engine `/docs`, `/openapi.json` | 200 in dev; off when `APP_ENV=production` (Q2, test `test_api_docs_follow_the_setting`) | PASS after fix |
| security | public-form rate limit | with the limit set to 5 (and the 60-s config cache waited out): `200 200 200 200 429 429 429 429` (the window already held one earlier submission from this address), and HTTP 200 again once the limit was back at 100. The first probe waited only 3 s and still ran against the cached 100 | PASS |


## 5. Bugs found and fixed

| # | Severity | Bug | Fix | Commit | Regression test |
|---|---|---|---|---|---|
| Q1 | **high (privacy)** | A free-text answer («صف آخر عمل») reached the language model unredacted: a phone, e-mail, ID or date typed there would have been sent | `redact_free_text()` runs the CV redaction over text answers before the judge (engine); the applicant's own name typed into a free answer is replaced by «[الاسم]» on the Frappe side before the answers leave the platform | talent-ai `40580f0`, ido_talent_ai `6df4aad` | `test_no_personal_data_in_any_model_payload`, `test_free_text_answer_redaction_keeps_the_evidence`, Frappe `test_free_text_answer_never_carries_the_applicant_name` |
| Q2 | low (security) | `/docs`, `/redoc`, `/openapi.json` of the engine readable without a login (no secrets; loopback + Tailscale only) | `API_DOCS_ENABLED`: on in dev, off when `APP_ENV=production`; documented in DEPLOY.md | talent-ai `591049a` | `test_api_docs_follow_the_setting` |
| Q3 | low (display) | A failed screening showed its stored 0 as a score in the applicant list (requested item) | list formatter shows «—» for `Failed`; the database keeps 0 | ido_talent_ai `6df4aad`, test `4666663` | Frappe `test_failed_score_shows_a_dash_in_the_list`; screen `docs/qa/screens/02_list_failed_shows_dash.png` |
| Q4 | harness | E2E K09 read the decision dialog object before it was shown; K15 polled the status before the retry call had set «Processing» — both races in `tools/ui/full_test.py`, not in the product (K15 passed in the rehearsal and when rerun) | wait for the modal / for the status to leave «Failed» | talent-ai (tooling commit) | the two cases themselves (rerun: PASS) |
| Q5 | low (access) | An HR User could read the engine settings through the API (`api.engine_settings`, `refresh_from_engine`: provider, model, callback URL, prompt — no secrets) although the settings screen refuses them; the document (p. 25) says HR Manager and System Manager only | both reads now require read permission on «AI Recruitment Settings» (`require_settings_access`) | ido_talent_ai `18c32e6` | Frappe `test_engine_settings_are_refused_to_hr_user`; live audit `audit_extras.json` 11/11 |
| Q6 | low (applicant feedback) | A 0-byte CV was saved as «no CV» and the applicant was never told the file was empty | the endpoint and the form refuse an empty file with «ملف السيرة فارغ — ارفع الملف الصحيح أو اتركه بدون سيرة», like a wrong type | ido_talent_ai `75c5aa6` | Frappe `test_empty_cv_file_is_refused_with_a_clear_message`; live follow-up (form and endpoint, nothing saved) |
| Q7 | **medium (availability)** | A restart of the engine's Redis made the four workers exit on the lost connection and none came back: every new screening would wait in the queue until someone started them by hand | `restart: on-failure` on the engine's api and worker containers (a clean stop stays stopped); documented in DEPLOY.md §3 | talent-ai `886bf5b` | live follow-up: Redis restarted mid-screening → workers back by themselves in 69 s, application assessed |
| Q7b | **medium (availability)** | Found with Q7: a screening created while Redis was unreachable stayed «queued» in the engine with no job behind it, and the host's retry got the same stuck screening back (an identical, non-failed screening is reused). The application would have stayed «Processing» until the 30-minute safety net | `dispatch_or_fail`: if the queue cannot take the job, the screening is marked failed («queue unavailable») and the API answers 503; the app retries into a new screening, and after its three attempts shows «Failed» with «إعادة المحاولة» | talent-ai `886bf5b` | engine `test_screening_is_not_left_queued_when_the_queue_is_down`; live follow-up with Redis stopped (§4) |
| Q9 | **medium (recovery)** | The hourly automatic retry never fired for an engine outage: since round 10 the failure is stored as the plain Arabic sentence, and the retry looked only for English words. An engine 5xx also put English text in HR's red bar («خطأ في محرك الذكاء 503: queue unavailable, try again»). The walkthrough (p. 26) says the evaluation «بيتعاد لوحده أو بزرار إعادة المحاولة» | a 5xx is now the same plain sentence as an unreachable engine (status and detail in the Error Log), and the hourly retry recognises that sentence | ido_talent_ai `cee20f7` | Frappe `test_engine_5xx_is_the_plain_sentence_for_hr`; the engine-down test now runs `retry_failed_jobs` and checks the application is queued again |

Effect on the document's numbers: only the test counts change (engine 135 → 139 + 1 skipped, Frappe 25 → 30; browser 40/40 unchanged), because every fix came with a regression test. The walkthrough PDF was not edited. Accuracy and speed: no change — the gold set after the fixes is identical judgement by judgement (315 + 18 judgements, 0 changed); the redaction keeps every number that is evidence (checked on the 5 free texts of the gold set and the 25 demo answers: 0 changed; only the deliberately personal sample changed).

## 6. Bugs not fixed and why

| # | Severity | Finding | Why not fixed | Proposed fix |
|---|---|---|---|---|
| Q8 | medium (evidence, English scans only) | On an English **scanned** CV the OCR misreads «Power BI» as «Power Bl» and «KPIs» as «KPls»; the English person-name detector (Presidio) then removes both, and «Data» from «Data Analyst» in the title line. The same CV as a text PDF keeps all three. It removes too much, never too little, so privacy is safe; the cost is CV evidence | Changing what the privacy filter removes is your decision, and it could change gold-set numbers (the analyst profile's CV quotes); recorded as OPEN_QUESTIONS #24 | an allow-list of skill and tool words checked before the name detector on Latin lines, then the gold-set rerun to show the numbers |
| L1 | limit | A scan turned 90° is not turned back: OCR confidence drops and the application goes to «Needs Review» with `low_ocr_confidence` (HR is told; nothing crashes) | turning on PaddleOCR's page-orientation step changes the OCR settings (ask first) and adds time per page | enable orientation classification for images, then rerun the OCR checks |
| L2 | limit | A job that Redis loses in a hard crash (snapshots every 60 s, no append-only file) stays «Processing» until the app's 30-minute safety net marks it Failed and the hourly retry re-screens it | rare (needs a Redis crash, not a restart); the recovery already exists | Redis append-only file, or an engine sweep that re-queues «queued» screenings older than a few minutes |
| L3 | cosmetic, platform code | The two remaining design notes are HRMS's own sticky mobile button on the job page (TEST_REPORT §8) | the platform's own code is never modified | none on our side |

Not bugs, recorded for completeness: the first exploratory run marked four cases FAIL because of the test harness (the CV details were read under the wrong key; the rate-limit probe waited 3 s although Frappe keeps the site config in memory for 60 s per web process; the HTML case expected the tags to be shown literally while Frappe's XSS filter strips them on save). The follow-up script checks them correctly.

## 7. What can only be verified after integration

- Accuracy on real applications: the expected levels of the gold set are computed from the rubric table, the free-text accuracy rests on 5 distinct texts; the client's HR must label 30–40 real applications (OPEN_QUESTIONS #13).
- Performance on the client's server: the 60 min per 1,000 is this server's GPU (Quadro RTX 6000, shared) with the 0.40 cap; a different GPU, a cloud model or scanned CVs change it (the load test had no scanned images).
- Real CV formats and quality: the synthetic set covers PDF (Arabic, English), Word, RTF, DOC, scans of three qualities, an encrypted and a corrupt file; real scanners, phone photos, multi-column templates and long CVs will differ.
- The production platform: version pinning, background workers, time zone, the dedicated API user (OPEN_QUESTIONS #1, #2, #8, #9), and the consent text (#7).
- Where the engine runs (PDPL, #4): decides whether real CVs may be processed at all.

## 8. Final state

`dev-frappe/reset_demo.sh` ran last (15:33–15:39) and the demo is clean:

| | |
|---|---|
| Applications | 27 |
| Processing | **0** |
| Completed / Needs Review / Failed | 23 / 2 / 0 |
| Awaiting consent / consent withdrawn (the two consent cases of the reset) | 1 / 1 |
| AI jobs | 26 Completed |

Engine and Frappe answer; every `talentai` container is up. Nothing else on the server was touched (no prune, no other builder, ports 18000–18099 only).

Commits on `p23-final-qa` (not pushed):

- talent-ai: `40580f0` (Q1), `591049a` (Q2), `886bf5b` (Q7, Q7b) and the documentation commit with this report, the QA tools and the regenerated test report.
- ido_talent_ai: `6df4aad` (Q1 name strip, Q3), `18c32e6` (Q5), `75c5aa6` (Q6), `cee20f7` (Q9), `4666663` (Q3 test).

Screens of the changed screens: `docs/qa/screens/` (three PNG files, synthetic data), also packed as `final-qa-screens.tar.gz` at the workspace root (not committed).
