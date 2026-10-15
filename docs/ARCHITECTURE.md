# Talent AI: architecture (v2, 2026-10-15)

This is the build reference for Claude Code. It merges the architecture agreed with Nadine (12-10-2026) and the v2 changes that follow the client's requirements document (`reference/client-requirements/IDO Recruitment AI.docx`, 13-10-2026). Where an older document disagrees with this file, this file wins. The Arabic version of the original architecture is the Claude Doc "معمارية الفرز الذكي للمتقدمين — Talent AI" and is kept only as history.

---

## 1. Goal in one paragraph

A security company receives hundreds or thousands of applications per job through a public Arabic web form on Frappe HRMS. HR cannot read them all carefully. Talent AI reads every application (form answers first, CV if attached), checks the job's hard eligibility rules, judges the applicant against criteria that HR approved, gives each judgement a quote or form answer as evidence, computes a score and a rank, and explains the result. HR reviews, overrides with a reason, and decides. The AI never rejects, shortlists or changes status.

## 2. Principles (each decision traces back to one of these)

1. **Engine knows no host system.** The engine speaks one neutral contract (job, candidate, document, screening). Frappe is one adapter. Any website, ERP or ATS can be another.
2. **Rules before the model.** Anything that can be checked with a number or a list (nationality, height, weight, age, file type) is checked in code.
3. **No judgement without evidence.** Every criterion judgement cites either a stored form answer or a literal quote from the redacted CV. Missing evidence is recorded as missing, never guessed.
4. **The model judges, code computes.** Score, coverage, band, rank, age and years of experience are computed in code. The model never outputs a final number.
5. **Minimum data.** The engine receives only the facts the rules need (age as a number, not birth date). National ID, photo and birth date stay in Frappe. The LLM sees redacted text only.
6. **Human decides.** HR changes status and can override any level with a written reason. Everything is logged.
7. **Every result is reproducible.** Each assessment stores the criteria version, model, prompt version and input hash. Same input + same versions = same result.

## 3. System overview

```
  Applicant (public web form, Arabic)
        |
        v
+----------------------- Frappe HRMS site ------------------------+
|  Job Opening (+ai_enabled, ai_profile, ai_profile_approved)     |
|  Job Applicant (+answers, facts, CV, ai_status, ai_score ...)   |
|  App: ido_talent_ai                                             |
|    - DocTypes: AI Recruitment Settings, AI Job Profile,         |
|      AI Job Criterion, AI Candidate Assessment,                 |
|      AI Assessment Evidence, AI Recruitment Job,                |
|      AI Recruitment Audit Log                                   |
|    - doc_events -> enqueue -> HTTP call to engine               |
|    - api.receive_result (HMAC callback)                         |
|    - HR screens: assessment section, ranking, compare, jobs     |
+-----------------------------|-----------------^-----------------+
                              | REST (API key)   | callback (HMAC)
                              v                  |
+------------------------- talent-engine ------------------------+
|  api (FastAPI)  ->  queue (Redis/RQ)  ->  worker(s)             |
|  Pipeline: intake > answers > CV text (OCR if scanned) >        |
|            redaction > structured profile > evidence check >    |
|            eligibility > criteria judgement > score/rank > index|
|  Postgres + pgvector  |  LLM gateway (LiteLLM)  |  OCR provider |
|  Talent Console (web UI for testing without any host system)    |
+-------------------|----------------------------|----------------+
                    v                            v
            vLLM (local, GPU)               PaddleOCR (local)
            [cloud providers: implemented, disabled]
```

Two repos:
- `talent-engine/`: the service (API, worker, pipeline, console, docker-compose, tests, evaluation).
- `ido_talent_ai/`: the Frappe app (fixtures, DocTypes, hooks, web form changes, HR UI, adapter client).

The engine is deployed separately (Docker). The Frappe app is installed into the client bench with `bench get-app` + `bench --site <site> install-app ido_talent_ai`. OCR and models live with the engine, never inside Frappe.

## 4. Pipeline (10 stages, in this order)

| # | Stage | What happens | Tool | Output |
|---|---|---|---|---|
| 1 | Intake | Receive the screening request, validate, dedupe by input hash, create a job record, enqueue | FastAPI + RQ | screening id (202) |
| 2 | Read form answers | Normalise the screening-question answers and facts. Blank ≠ 0: a blank answer is "not answered" (missing evidence); `0` is a real answer | code | answers map |
| 3 | Extract CV text | Only if a CV exists. Text PDF → PyMuPDF; DOCX → python-docx; DOC/RTF → LibreOffice headless; scanned PDF or image → OCR. Corrupt/unreadable → stage marked failed, screening continues on answers only with flag `cv_unreadable` (never a Failed screening) | PyMuPDF, python-docx, LibreOffice, OCRProvider | text + method + OCR confidence |
| 4 | Redaction | Remove name, phone, email, national ID/iqama, address, nationality, gender words, age/birth date, photo references **before any LLM call** | Presidio + Saudi/Arabic regex patterns | redacted text + redaction report |
| 5 | Structured profile | LLM turns redacted text into a typed profile (experience items with dates, certifications, skills, languages). Every item carries the quote it came from | LLM (structured output) + Pydantic | CandidateProfile |
| 6 | Evidence check | Drop any item whose quote is not literally in the redacted text (fuzzy match ≥ 0.9 after normalising Arabic letters/digits). Years computed in code from dates. Answer vs CV contradiction → keep the lower value, flag "contradiction", needs review | code + rapidfuzz | verified profile |
| 7 | Eligibility (hard rules) | Evaluate the job's rules on declared facts, no LLM. Outcomes: eligible / not eligible (as declared) / needs review (value missing) | code (own evaluator over rule rows `fact / operator / value`, operators in, not_in, >=, <=, >, <, ==, !=, between; no json-logic dependency, decided in phase 1) | eligibility + reasons |
| 8 | Criteria judgement | For each approved criterion, the LLM picks a level 0/25/50/75/100 using the written rubric and cites evidence (form field or CV quote). Temperature 0. The LLM never sees rules, nationality, age, gender or name | LLM (structured output) | level + evidence per criterion |
| 9 | Score and rank | `score = Σ(weight% × level) / 100`, coverage, band, flags, rank within the job; strengths, gaps, "what would raise the score" (exact points) | code | ScreeningResult |
| 10 | Index | Embed the verified profile for the talent pool (only if consent and retention allow) | Qwen3-Embedding-0.6B + pgvector | vector |

If there is no CV, stages 3–6 are skipped and shown as "no CV, assessed from answers only".

## 5. Scoring model (v2)

- Each **AI Job Criterion** has: text, `weight` (percent), `mandatory` (bool), and a **rubric**: one written description for each level 0, 25, 50, 75, 100. Example for "supervision experience": 0 = none, 25 = acted as team lead occasionally, 50 = < 2 years formal supervision, 75 = 2–5 years, 100 = > 5 years or supervised ≥ 20 guards.
- Weights must total exactly 100%. Approving a profile with another total is blocked (server-side validation, not only UI).
- `score = Σ(weight_i × level_i) / 100` → 0–100, one decimal.
- **Missing evidence** on a criterion → level 0, flag `missing_evidence` ("دليل ناقص"). It is not treated as proof of incompetence: it lowers coverage and triggers review.
- `coverage = Σ weight_i where evidence exists`. Shown as a percent.
- **Band**: high ≥ 75, medium 50–74.9, low < 50.
- A **mandatory** criterion judged level 0 **with evidence** → band forced to low.
- A mandatory criterion with **missing** evidence, or coverage < 60% → `ai_status = Needs Review` (clarification that follows client doc §7: missing information is never treated as failure). Confirmed by Nadine 2026-10-15; the demo README omits the mandatory-missing case, this file wins.
- Sentence shown wherever a score appears: «الدرجة ترتيب مقابل معايير معتمدة، وليست احتمال نجاح في الوظيفة».
- **Flags** used by the engine: `missing_evidence`, `contradiction`, `low_ocr_confidence`, `cv_unreadable`, `duplicate`, `stale`. A screening is **Failed** only when the engine itself fails (LLM, OCR, DB, timeout) after 3 attempts. An unreadable or corrupt CV never fails a screening (decided 2026-10-15). The clickable demo still shows the older "Failed after 3 attempts" behaviour for a corrupt CV; this file wins.

**Who is ranked** in a job: only assessments that are Completed, eligible, current (same profile version, applicant data unchanged since evaluation) and not duplicates. Everything else is listed in collapsed groups with the reason (not eligible, needs review, processing, failed, stale, duplicate).

**Worked example (must pass as a unit test), "مشرف أمن" profile:**

| criterion | mandatory | weight | level | w × level |
|---|---|---|---|---|
| خبرة الإشراف | yes | 30 | 75 | 2250 |
| الخبرة الأمنية | yes | 20 | 100 | 2000 |
| إدارة الورديات | no | 15 | 100 | 1500 |
| رخصة حارس أمن | no | 15 | 100 | 1500 |
| كتابة التقارير | no | 8 | 50 | 400 |
| إسعافات أولية | no | 7 | 0 | 0 |
| اللغات | no | 5 | 100 | 500 |
| total | | 100 | | 8150 → **81.5**, coverage 100%, band high |

Client doc example (also a unit test): 40%×90 + 35%×80 + 25%×100 → 89.

## 6. Hard eligibility rules

Stored per AI Job Profile as rows: `fact`, `operator`, `value`, `if_missing` (always `review`). Facts come from the form, self-declared. Demo profile "مشرف أمن":

| fact | operator | value |
|---|---|---|
| nationality | in | [Saudi Arabia] |
| height_cm | >= | 180 |
| weight_kg | <= | 80 |
| age | >= | 18 (placeholder until the client gives the real value) |

- Fail on a declared value → «غير مستوفٍ حسب التصريح»: not ranked in this job, kept in the talent pool, never auto-rejected.
- Missing value → «يحتاج مراجعة».
- Age is computed in Frappe from date of birth; only the integer is sent.
- UI never shows raw operators (`>=`, `in`); it renders Arabic sentences («الطول 180 سم أو أكثر»).

## 7. Engine data model (Postgres)

| table | key fields |
|---|---|
| tenant | id, name, api_key_hash, callback_url, callback_secret, ai_provider, ai_model, ocr_provider, llm_timeout_s, max_retries, retention_days (the effective settings; read and written through `/v1/settings`) |
| job | tenant_id, external_ref, title, description, active_version |
| job_version | job_id, version, criteria (json: text, weight, mandatory, rubric), rules (json), questions (json), approved_by, approved_at |
| candidate | tenant_id, external_ref, id_token (HMAC-SHA256 of the national ID, computed by the adapter with a secret the engine never sees; used only for duplicate detection), facts (json: only allowed facts), answers (json), consent, retention_until, data_hash |
| document | candidate_id, kind (cv), mime, sha256, text, extraction_method, ocr_confidence, redacted_text |
| profile | candidate_id, schema_version, data (json with quotes) |
| screening | job_version_id, candidate_id, status, eligibility, eligibility_reasons, score, coverage, band, flags, rank, summary, strengths, gaps, versions (model, prompt, schema), input_hash, attempts, error |
| criterion_result | screening_id, criterion_key, level, source (form_field / cv_quote), field, evidence_text, missing_evidence, overridden_level, override_reason, override_by |
| embedding | candidate_id, vector (pgvector), model |
| audit_event | tenant_id, ref, action, actor, at, payload |

CV files are stored on disk/volume with sha256 names, not in the DB. The engine stores no names, national IDs or photos. All timestamps are stored in UTC (`timestamptz`); host systems convert for display (the local dev Frappe site runs on Asia/Riyadh).

## 8. API (engine)

Auth: `Authorization: Bearer <tenant api key>`. OpenAPI generated by FastAPI. JSON only. Versioned under `/v1`.

| method + path | purpose |
|---|---|
| `PUT /v1/jobs/{ref}` | create/update a job and its approved version (criteria, rules, questions). Rejects weights ≠ 100 |
| `POST /v1/jobs/draft-criteria` | draft description + criteria + rubric + weights from a title/description, for HR to edit and approve |
| `PUT /v1/candidates/{ref}` | upsert candidate facts, answers, consent; files as multipart or URL |
| `POST /v1/screenings` | screen candidate × job. Returns 202 + id. Result is pushed to the callback |
| `GET /v1/screenings/{id}` | status and full result |
| `GET /v1/jobs/{ref}/ranking` | ranked list + grouped non-ranked with reasons |
| `POST /v1/jobs/{ref}/rescreen` | rescreen all candidates of a job after a new version |
| `POST /v1/screenings/{id}/override` | HR level override with reason (recomputes score) |
| `POST /v1/talent-pool/search` | past candidates for a job (hard rules first, then semantic similarity; excludes withdrawn consent / expired retention) |
| `DELETE /v1/candidates/{ref}` | full erasure (documents, profile, vectors, results) |
| `GET /health`, `GET /ready` | liveness/readiness (DB, Redis, LLM, OCR) |
| `GET /v1/settings` | the tenant's effective AI/OCR settings (provider, model, ocr_provider, timeout, max_retries). The engine owns these values |
| `PUT /v1/settings` | change them (validated; `cloud` refused while no key is configured). The Frappe settings screen is a client of these two endpoints; `.env` holds defaults for new tenants only |

Callback: `POST {callback_url}` with headers `X-Talent-Signature: sha256=<HMAC-SHA256 of "<timestamp>.<body>" with callback_secret>`, `X-Talent-Timestamp` (unix seconds) and `X-Talent-Event`. The timestamp is part of the signed message so it cannot be swapped on replay. Receiver rejects a bad signature or a timestamp older than 5 minutes. Retries with backoff (3 attempts).

Result shape:

```json
{
  "screening_id": "scr_01J...",
  "job_ref": "HR-OPN-2026-0004",
  "job_version": 4,
  "candidate_ref": "HR-APP-2026-00123",
  "status": "completed",
  "eligibility": "eligible",
  "eligibility_reasons": [],
  "score": 81.5,
  "coverage": 1.0,
  "band": "high",
  "flags": [],
  "criteria": [
    {"key": "supervision", "weight": 30, "mandatory": true, "level": 75,
     "source": "form_field", "field": "q_supervision_years", "evidence": "4",
     "missing_evidence": false, "confirmed_by_cv": true}
  ],
  "summary": "...", "strengths": ["..."], "gaps": ["..."],
  "raise_score": [{"criterion": "first_aid", "points": 7.0}],
  "versions": {"model": "qwen3-8b-awq", "prompt": "judge-v1", "profile_schema": "1.0"},
  "input_hash": "sha256:..."
}
```

**Adapter contract** (any host system implements this):

```python
class SourceAdapter(Protocol):
    def get_job(self, ref: str) -> JobIn: ...
    def get_candidate(self, ref: str, needed_facts: set[str]) -> CandidateIn: ...
    def get_documents(self, ref: str) -> list[DocumentIn]: ...
    def push_result(self, result: ScreeningOut) -> None: ...
```

An MCP server (MCP Python SDK) exposes the same operations as tools for AI agents. Phase 2 or later.

## 9. Frappe app `ido_talent_ai`

Rule: **no edits to frappe/erpnext/hrms code.** Everything is DocTypes, Custom Fields and Property Setters exported as fixtures, hooks, and app pages. Before creating a field, check it does not already exist on the site (the client asked for this).

### 9.1 DocTypes (client names; our additions marked +)

| DocType | type | fields |
|---|---|---|
| AI Recruitment Settings | Single | provider (local/cloud), model, timeout, max_retries: **read from and written to the engine** through `/v1/settings` (the engine owns them; Frappe keeps the last value only for display). Stored in Frappe: enabled, + engine_url, + api_key (Password), + callback_secret (Password), + id_token_secret (Password, for the national-ID HMAC), + auto_screen_on_apply, + allowed_facts |
| AI Job Profile | normal | job_opening (Link), version, approved, approved_by, approved_on, criteria (Table AI Job Criterion), + rules (Table), + questions (Table), + copied_from_designation; button «نسخ من قالب المسمى الوظيفي» and «اقتراح معايير AI» |
| AI Job Criterion | child | criterion, weight (Percent), description, + mandatory, + rubric_0/25/50/75/100 |
| AI Candidate Assessment | normal | applicant, job_opening, profile_version, score, status, summary, evidence (Table AI Assessment Evidence), + eligibility, + coverage, + band, + flags, + rank, + strengths, + gaps, + model, + prompt_version, + input_hash, + stale |
| AI Assessment Evidence | child | criterion, score (level), evidence_text, missing_data, + source (form_field / cv_quote), + field, + overridden_level, + override_reason, + override_by |
| AI Recruitment Job | normal | reference_doctype, reference_name, job_type, status, error_message, + attempts, + engine_screening_id |
| AI Recruitment Audit Log | normal | reference, action, actor, timestamp, version, + reason |

### 9.2 Custom fields

- Job Opening: `ai_enabled` (Check), `ai_profile` (Link AI Job Profile), `ai_profile_approved` (Check, read-only).
- Job Applicant: `ai_status` (Select: Processing / Completed / Needs Review / Failed), `ai_score` (Percent), `ai_assessment` (Link), `ai_evaluated_on` (Datetime), plus the application facts the form collects: nationality, id_type, national_id (permlevel 1; the raw value never leaves Frappe: the adapter sends only `id_token = HMAC-SHA256(national_id, id_token_secret)` for duplicate detection), date_of_birth, height_cm, weight_kg, photo, certificates (table), ai_consent, and a child table for screening-question answers.
- Check `reference/discovery/04_fields_matrix.csv` first: some fields already exist on the site.

### 9.3 Web form

Discovery (2026-10-12) found only the standard `job-application` web form on the demo site; openings use the default form (`job_application_route` empty). The name `job-application-ksa` appears only in the clickable demo and must not be assumed to exist. We create our own web form (`ai-job-application`) and point `Job Opening.job_application_route` to it for AI-enabled jobs; the standard form is never edited. Arabic by default. Screening questions come from the job's approved AI Job Profile and render dynamically. Height/weight appear only if the job has those rules. CV optional (PDF, DOCX, JPG, PNG; size limit agreed with Frappe team). Consent checkbox required. Hint under numeric questions: «اكتب 0 إذا لا توجد خبرة. الفراغ يعني لم يُجب». See `reference/discovery/06_web_form.md`.

### 9.4 Flow

1. Applicant submits → Job Applicant created (this must always succeed, even if the engine is down: acceptance test 6).
2. `doc_events.Job Applicant.after_insert` → if the job's `ai_enabled` and `ai_profile_approved` → create AI Recruitment Job, set `ai_status=Processing`, `frappe.enqueue` (queue `long`).
3. Worker builds the payload (only allowed facts, answers, CV file) and calls `PUT /v1/candidates` + `POST /v1/screenings`.
4. Engine calls back `ido_talent_ai.api.receive_result` (allow_guest + HMAC check) → write AI Candidate Assessment + evidence, update applicant fields, log.
5. `on_update` of Job Applicant: if answers or facts changed after evaluation → mark assessment stale, show «النتيجة لا تعكس آخر تعديل», remove from ranking until rescreen.
6. Approving a new AI Job Profile version → older assessments stale, button «إعادة تقييم الكل».
7. A scheduled job (hourly) retries Failed jobs up to `max_retries` and marks timed-out Processing jobs Failed. This needs the scheduler; if it is off on the target site, retries are manual from the jobs screen.

### 9.5 HR screens

- Job Applicant form: section «تقييم الذكاء الاصطناعي» (eligibility, score, band, coverage, rank, summary, criteria table with level + evidence, CV panel with quote highlighting, strengths/gaps, raise-score), buttons Shortlist / Hold / Reject (reason required for Reject and overrides), «إلغاء حكم الذكاء» per criterion.
- Job Applicant list: columns and filters for ai_status, ai_score, band, eligibility, job.
- Ranking page per Job Opening: ranked list, grouped non-ranked, compare 2–3 side by side (phase 2 feature 10), CSV export UTF-8 with BOM.
- AI jobs screen (list of AI Recruitment Job with retry).
- Talent pool search from a Job Opening (phase 2 feature 13).
- Roles: HR Manager / HR User can act; others see nothing of the AI section.

The UX target is `reference/demo/talent-ai-demo.html`.

## 10. AI layer

- **Gateway**: one OpenAI-compatible client (`openai` SDK) for both providers: `local` points at vLLM inside the compose network, `cloud` at any OpenAI-compatible endpoint with a key. LiteLLM was not needed for this (decided in phase 3; it can be added later if a cloud provider is not OpenAI-compatible). `AI_PROVIDER=local|cloud` in `.env` is only the default for a new tenant; the effective provider and model per tenant live in the engine DB and are changed through `/v1/settings`. Local is the default and the only one enabled now.
- **Local serving**: vLLM (`vllm/vllm-openai` image) as compose service `vllm`, port 8000 exposed only inside the compose network (no host port), weights in the `talentai_models` volume (`HF_HOME`), `--gpu-memory-utilization 0.40` (agreed cap on the shared Quadro RTX 6000, 24 GB, Turing: AWQ int4 weights, fp16 compute, no FP8/bf16).
- **Model candidates** (pick by evaluation, not by preference): Qwen3-8B-AWQ (start here), Qwen3-14B-AWQ (if memory allows), Command R7B Arabic, ALLaM-7B. Thinking mode off for judging.
- **Structured output**: Pydantic schemas sent as `response_format=json_schema` (guided decoding on vLLM, native JSON mode on cloud APIs). Invalid JSON → one repair retry → else the screening attempt fails (engine error, retried up to max_retries). Temperature 0; Qwen3 thinking mode off (`chat_template_kwargs.enable_thinking=false`, sent to vLLM only).
- **Judgement contract** (`judge-v1`): per criterion the model returns `form_level` + `form_value` (from the stored answer) and `cv_level` + `cv_quote` (from the redacted CV). Code verifies both (answer must equal the stored value, quote must exist with fuzzy ratio ≥ 0.9 after Arabic normalisation), takes the lower level on a contradiction and flags it, marks `confirmed_by_cv` when the CV agrees, and drops anything unverifiable (flags `evidence_mismatch`, `quote_not_found`).
- **Profile contract** (`profile-v1`): experience items with dates as written and a literal quote each, certifications with status, languages, education. Years, supervision years and team sizes are computed in code from the verified items and handed to the judge as facts.
- **Prompts**: files in `talent-engine/prompts/` with a version id (`profile-v1`, `judge-v1`, `draft-criteria-v1`). The version is stored on each result. Prompt changes require the evaluation to be rerun.
- **Embedding / rerank**: Qwen3-Embedding-0.6B (+ Qwen3-Reranker-0.6B if needed), run on CPU or small GPU share.
- **Tracing**: Langfuse self-hosted (optional, phase after core) or structured logs with the same fields.

## 11. OCR

- `OCRProvider` interface: `extract(file) -> pages[{text, confidence}]`.
- Implementations: `paddle_vl` (PaddleOCR-VL on GPU, best for Arabic + layout; phase 3), `paddle_cpu` (PaddleOCR 3.x on CPU: `PP-OCRv5_mobile_det` + `arabic_PP-OCRv5_mobile_rec`, with a second pass of `en_PP-OCRv5_mobile_rec` merged per text box because the Arabic recogniser drops digits, e-mails and dates; `enable_mkldnn=False` because paddlepaddle 3.3's oneDNN path crashes; ~20 s per page on 8 threads; implemented in phase 2), `fake` (tests), `cloud` (stub, disabled), `none`. Models live in the `models` volume, downloaded on first use.
- Used only when the PDF has no text layer or the file is an image.
- Confidence = text-length-weighted mean of recogniser scores (punctuation-only boxes ignored). Low confidence (< `OCR_MIN_CONFIDENCE`, 0.80 until phase 4 calibrates it) → flag `low_ocr_confidence`, needs review.
- Extraction and redaction run **at upload time** (`PUT /v1/candidates/{ref}/cv`), so the applicant's name hint is used once for redaction and never stored anywhere (not even in a queue). The pipeline's stages 3–4 then report what was stored. A new CV changes the candidate's data hash → earlier results become stale.
- No training. Off-the-shelf models only.

## 12. Privacy, security, compliance

- Saudi PDPL applies. The client is the controller. Cloud LLM/OCR only with the client's written approval. **Open question: where the GPU server physically is.** If it is outside KSA, processing real CVs on it is a cross-border transfer and needs approval. Until answered: synthetic data only.
- Consent is mandatory on the form; consent text versioned.
- Data minimisation: allowed facts list in settings; engine rejects unknown facts.
- The raw national ID never reaches the engine. For duplicate detection the adapter sends `id_token = HMAC-SHA256(national_id, id_token_secret)`; the secret stays in Frappe (Password field), so the engine cannot reverse the token.
- Redaction before LLM; logs contain no raw CV text or personal data (hashes and ids only).
- Secrets in `.env` (engine) and Password fields (Frappe). Never committed.
- Retention per tenant; deletion endpoint removes everything; talent pool honours consent withdrawal and retention.
- Blind judging: the model never receives name, nationality, gender, age, photo. Periodic name-swap test (same CV, different names → same result).
- Applicants never see AI scores.

## 13. Configuration (`talent-engine/.env.example`)

Defaults only: provider, model and OCR values are per tenant in the DB and are changed through `/v1/settings`. The Talent Console is served by the API process under `/console` on `API_PORT`; there is no separate console port (decided 2026-10-15).

```
APP_ENV=dev
TZ=UTC
API_PORT=18000
DATABASE_URL=postgresql://talentai:***@db:5432/talentai
REDIS_URL=redis://redis:6379/0
AI_PROVIDER=fake          # fake = deterministic rubric provider (phase 1, tests); local from phase 3
LLM_BASE_URL=http://vllm:8000/v1
LLM_MODEL=qwen3-8b-awq
LLM_TIMEOUT_S=120
LLM_MAX_RETRIES=2
VLLM_GPU_MEMORY_UTILIZATION=0.35
CLOUD_LLM_MODEL=
CLOUD_LLM_API_KEY=
OCR_PROVIDER=paddle_cpu
OCR_MIN_CONFIDENCE=0.80
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
FILE_STORE=/data/files
RETENTION_DAYS_DEFAULT=365
```

## 14. Testing and evaluation (summary; details in TESTING.md)

- Unit tests: scoring (both worked examples), coverage, bands, mandatory rule, eligibility outcomes, blank vs 0, evidence check, redaction patterns, HMAC.
- Integration: full pipeline with a fake LLM (deterministic) and with the real local LLM.
- Gold set: 50–100 synthetic applications for two jobs, labelled by hand (later reviewed by the client's HR). Metrics: evidence present 100%, quotes verified 100%, extraction accuracy ≥ 90%, agreement with HR top-10, same result on rerun, name-swap invariance, time per application and per 1000 on this server.
- Acceptance: the client's 8 criteria (TESTING.md).

## 15. Out of scope now (do not build, do not stub)

AI interview questions (06), smart/voice interview (07), technical assessments (08), interview summary (09), job-offer draft (11), applicant portal (12), recruitment dashboard (14). Comparison (10) and talent pool (13) are phase 2.
