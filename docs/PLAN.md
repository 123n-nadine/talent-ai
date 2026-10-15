# Build plan

Work one phase at a time. At the end of each phase: all tests green, update the Status section in `CLAUDE.md`, then **stop** and give Nadine a short message in Egyptian Arabic: what was built, how to try it (exact commands / URLs), what is still missing. Wait for her OK.

Branch per phase in the relevant repo (`phase-0-setup`, `phase-1-core`, …). Nadine merges into `main`.

---

## Phase 0: inspect the server and set up the workspace (read-only first)

Goal: know exactly what we are working with on a **shared** machine before installing anything.

1. Report, without changing anything:
   - OS and kernel, CPU, RAM, free disk on the partition of this folder.
   - `nvidia-smi`: GPU model, driver, CUDA version, total/used/free memory, which processes use the GPU (and which user, if visible).
   - Docker and Docker Compose versions; is the current user in the `docker` group; is the NVIDIA container toolkit configured (`docker info | grep -i runtime`). Do not pull images yet.
   - `docker ps --format '{{.Names}} {{.Image}} {{.Ports}}'`: what colleagues already run (names, images, ports only). Note any existing LLM server (vLLM, Ollama, TGI) or Postgres/Redis.
   - Ports in use (`ss -ltn`) and confirm 18000–18099 are free.
   - Python versions available, `uv`/`pip` availability, Node version.
   - Is Frappe installed anywhere? (`which bench`, look for `frappe-bench` directories under home and `/opt`, Frappe images in `docker images`). Read only. Our own dev bench will be separate anyway.
   - Outbound network: can we reach pypi.org, huggingface.co, github.com, registry-1.docker.io (simple HEAD requests).
2. Write the findings to `docs/SERVER_REPORT.md` with a recommendation: how much GPU memory we can safely use, which ports, Docker vs no Docker, anything that needs `sudo` (list it, do not run it).
3. Create the workspace layout from `CLAUDE.md`. Two repos: `talent-ai` (the workspace itself, with `talent-engine/` inside; ignores `ido_talent_ai/`, `dev-frappe/`, `.env`, `data/`, `models/`) and `ido_talent_ai` (app at the repo root). Each with a README, `.gitignore` (Python, Node, `.env`, `data/`, `models/`, `*.pdf` in data dirs), license placeholder, and a pre-commit config (ruff + ruff-format, mypy light).
4. Remotes: `git@github.com:123n-nadine/talent-ai.git` and `git@github.com:123n-nadine/ido_talent_ai.git` (private, branch `main`). Push only after Nadine confirms the SSH key is registered on GitHub.

**Nadine checks:** reads SERVER_REPORT.md, agrees on the GPU memory cap and ports, gives repo URLs.

---

## Phase 1: engine core, no AI yet

Goal: the full pipeline skeleton works end to end with a **fake LLM** and form answers only. Every number is already correct.

- `talent-engine` structure: `app/api`, `app/core` (config, security), `app/domain` (Pydantic models), `app/pipeline/stages/*`, `app/rules`, `app/scoring`, `app/llm` (gateway + fake provider), `app/ocr` (interface only), `app/storage`, `app/worker`, `console/`, `prompts/`, `tests/`, `eval/`.
- Docker Compose project `talentai`: api, worker, db (postgres 16 + pgvector), redis. Ports from SERVER_REPORT.
- Alembic migrations for the data model in ARCHITECTURE §7.
- Endpoints: jobs (PUT, validation weights = 100), candidates (PUT), screenings (POST/GET), ranking (GET), rescreen, override, delete, settings (GET/PUT; engine-owned provider/model/OCR values), health/ready. API key auth. HMAC callback sender (to a configurable URL; a local test receiver is enough).
- Stages implemented for real: intake, read answers (blank ≠ 0), eligibility (json-logic, three outcomes, Arabic reason sentences), scoring (formula, coverage, bands, mandatory rule, needs-review rule), ranking (only current + eligible + completed; grouped others), stale detection (data_hash and job version), duplicates (same candidate ref or same `id_token`, the HMAC-SHA256 of the national ID computed by the adapter; the raw ID never reaches the engine), strengths/gaps/raise-score.
- Fake LLM: deterministic judgement from form answers using the rubric thresholds, so the pipeline runs without a GPU.
- Seed script: the "مشرف أمن" profile (weights 30/20/15/15/8/7/5, rules, questions) and ~25 synthetic applicants copied from the demo's data spread (strong, medium, low, needs review, not eligible, duplicate, contradiction).
- Tests: both worked examples (81.5 and 89), every rule outcome, blank vs 0, stale, duplicates, ranking groups, HMAC, weights ≠ 100 rejected.

**Nadine checks:** `docker compose -p talentai up`, opens the OpenAPI page, runs the seed, calls ranking and sees the same order as the demo for the same data; `make test` green.

---

## Phase 2: reading documents (text, OCR, redaction)

- Text extraction: PyMuPDF (text PDF), python-docx (DOCX), LibreOffice headless (DOC/RTF → PDF/text). Detect "no text layer" → OCR.
- `OCRProvider`: `paddle_cpu` first (works without GPU), then `paddle_vl` on GPU behind the same interface. Confidence per page. Model files in a volume, not in git.
- Corrupt/unreadable file → stage failed, screening continues from answers with flag `cv_unreadable`; the screening is never Failed because of the file.
- Redaction: Presidio + custom recognisers (Saudi national ID/iqama 10 digits starting 1/2, +966/05 phones, emails, Arabic and English names from the applicant's own name field sent as a hint and never stored, nationality and gender words, dates of birth, addresses). Unit tests with Arabic and English samples. Report of what was removed.
- Synthetic test CVs: generate 20 (Arabic/English, PDF text, DOCX, scanned image made by rendering a PDF to an image with noise/rotation).

**Nadine checks:** uploads a scanned Arabic CV from the console, sees extracted text, OCR confidence and the redacted version with nothing personal left.

---

## Phase 3: local LLM

- Check free GPU memory again. Propose the vLLM command (model, `--gpu-memory-utilization`, `--max-model-len`, quantization) and **wait for Nadine's OK before downloading the model** (> 5 GB rule). Agreed starting cap: `--gpu-memory-utilization 0.40` (SERVER_REPORT option A); Nadine confirms Luna's GPU need with awais before this phase.
- vLLM service in the compose project (GPU reserved via `deploy.resources.reservations.devices`), OpenAI-compatible.
- LiteLLM gateway: `local` wired; `cloud` implemented but disabled by default.
- Prompts `profile-v1` (structured profile with quotes), `judge-v1` (level per criterion with rubric + evidence), `draft-criteria-v1` (description + criteria + rubric + weights summing to 100, as a draft only). Guided JSON; one repair retry.
- Evidence check stage (quote must exist; years from dates in code; answer-vs-CV contradiction).
- Swap the fake LLM for the real one by config; keep the fake for tests.

**Nadine checks:** screens 5 synthetic applicants with the real model, opens each result and confirms every level has evidence and no invented skills.

---

## Phase 4: gold set and evaluation

- `eval/gold/`: 50–100 synthetic applications for "مشرف أمن" and one non-security job, with expected levels per criterion and expected eligibility, labelled by hand (Nadine reviews the labels).
- `eval/run.py`: runs the gold set, reports per-metric results (see TESTING.md §3) and time per application; saves a dated report in `eval/reports/`.
- Compare at least two local models (Qwen3-8B-AWQ vs one Arabic model) and two prompt versions. Name-swap invariance test.
- promptfoo (or pytest-based) regression so prompt changes are measured.

**Nadine checks:** reads the evaluation report and picks the model.

---

## Phase 5: Talent Console (test the full cycle without Frappe)

- A small web UI served by the engine (`/console`), Arabic RTL first, styled like `reference/demo/talent-ai-demo.html`, but calling the **real API**.
- Screens: job profile (criteria, rubric, weights with 100% check, rules, questions, draft with AI, approve → new version), application form (same fields as the real form, CV optional, consent), processing view (live stage-by-stage status from the API), applicants list, applicant result (levels, evidence, CV panel with quote highlight, override with reason), ranking with groups, AI jobs with retry, settings (provider, model, OCR provider, read and written through `/v1/settings`), audit log.
- Developer toggle that shows the request/response JSON.

**Nadine checks:** runs the whole cycle herself, start to finish, using TESTING.md §1. This is the gate before touching Frappe.

---

## Phase 6: Frappe app on our own local bench

- `dev-frappe/`: Docker-based dev bench matching the client versions from `reference/discovery/01_environment.md` (Frappe 16.31.x, ERPNext 16.32.x, HRMS develop 17.0.0-dev: pin to the develop HEAD on the day the bench is built and record the commit in `dev-frappe/VERSIONS.md`; the production commit is requested from the Frappe team, see `docs/OPEN_QUESTIONS.md`). Separate compose project (`talentai-frappe`), ports 18050–18059. Create a test site with time zone Asia/Riyadh, country Saudi Arabia, default language Arabic.
- Recreate what the client site has that we depend on: the standard `job-application` web form as found in discovery (no client-specific form exists on the demo) and the custom fields found in discovery (from `reference/discovery/03_doctypes/` and `04_fields_matrix.csv`), so our app is tested against the same shape.
- `ido_talent_ai`: DocTypes, custom fields and property setters as fixtures, our web form, hooks, enqueue, adapter client, `api.receive_result` with HMAC, HR screens (assessment section, list columns/filters, ranking page, AI jobs, settings), roles/permissions, Arabic translations (`translations/ar.csv`).
- Frappe tests for hooks, callback, permissions and the "engine down" case.

**Nadine checks:** submits an application on the local site's web form and sees Processing → Completed with the result in the Job Applicant form and the ranking page.

---

## Phase 7: acceptance and portability

- Run the client's 8 acceptance criteria on the local bench (TESTING.md §2) and record evidence (screenshots, logs) in `docs/ACCEPTANCE_REPORT.md`.
- Clean-install rehearsal: fresh bench + site → `bench get-app` from the repo URL → `install-app` → migrate → works with no manual steps. Then uninstall and confirm nothing of the platform is broken.
- Fill `DEPLOY.md` for the real platform from `docs/DEPLOY_CHECKLIST.md`.

**Nadine checks:** signs off phase 1 delivery. Only then is anything connected to the client's demo site, through the Frappe team.

---

## Phase 8 (after sign-off): client features 10 and 13

- Candidate comparison screen (criteria-level, evidence, incomplete results shown clearly).
- Talent pool: embeddings, `talent-pool/search`, hard rules first, consent and retention exclusions, suggestion only.
