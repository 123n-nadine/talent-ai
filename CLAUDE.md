# Talent AI — project memory for Claude Code

Read this file fully at the start of every session. Then read `docs/PLAN.md` to see the current phase.

## Who you work with
- **Nadine** (AI engineer, i-do Holding) owns this project. She builds it; you implement with her.
- **Talk to Nadine in simple Egyptian Arabic** (colloquial, short sentences, no jargon without a one-line explanation). When mixing Arabic and English, start each line with an Arabic word and put English terms at the end of the line or on their own line.
- Code, comments, commit messages and technical docs are in **English**. UI text shown to HR/applicants is **Arabic first** (RTL) with an English toggle.

## What we are building
An AI screening and ranking layer for the **recruitment module of a Frappe HRMS platform** used by a Saudi security company (client platform: `secure4security.ido.sa`; demo environment: `demo.hs1.ido.sa`). When ~1000 people apply for a job, the system reads each application, checks hard eligibility rules, judges the applicant against HR-approved criteria with evidence, scores and ranks them, and explains why. **HR always makes the final decision.**

It must be **reusable**: a standalone engine that any system can plug into through a small adapter. Frappe is only the first adapter.

Two deliverables, two git repos:
1. **`talent-ai`** (this workspace, `git@github.com:123n-nadine/talent-ai.git`) — holds `CLAUDE.md`, `docs/`, `reference/` and **`talent-engine/`**: the standalone FastAPI service (+ worker, DB, OCR, local LLM), with its own **Talent Console** web UI so Nadine can test the whole cycle without Frappe.
2. **`ido_talent_ai/`** (separate repo, `git@github.com:123n-nadine/ido_talent_ai.git`; git-ignored by the workspace repo because `bench get-app` needs the app at the repo root) — a Frappe app installed on the platform with `bench get-app` + `install-app`. It adds DocTypes, custom fields, the application web form, hooks and HR screens, and talks to the engine over HTTP. **The platform's own code is never modified.**

Full design: `docs/ARCHITECTURE.md`. Build order and checkpoints: `docs/PLAN.md`. How Nadine tests: `docs/TESTING.md`. Rules that make the move to the real platform safe: `docs/DEPLOY_CHECKLIST.md`. Server facts and agreed ports/GPU cap: `docs/SERVER_REPORT.md`. Questions still waiting for an answer: `docs/OPEN_QUESTIONS.md`.

## Decisions already made (do not reopen without asking Nadine)
1. **Application-form answers are the primary data source.** Each job has screening questions. The CV is optional; OCR runs only on scanned CVs.
2. **Weights are percentages that must total 100%.** Each criterion is judged on fixed levels **0 / 25 / 50 / 75 / 100** with a written rubric. `score = Σ(weight% × level) / 100`.
3. **Hard eligibility rules** (nationality, height, weight, age…) are code rules, separate from scoring. The LLM never sees nationality, gender, age, name, photo or IDs. The raw national ID never leaves Frappe: the adapter sends only `id_token = HMAC-SHA256(national_id, id_token_secret)` for duplicate detection.
4. **Redaction happens before any LLM step.**
5. **Every judgement needs evidence**: either a form answer (must equal the stored answer) or a literal quote from the redacted CV (must exist in the text). Missing evidence = level 0 + "missing evidence" flag, never a guess.
6. **The LLM judges, code computes.** Scores, ages, years of experience, coverage, bands and ranks are computed in code.
7. **AI never changes an applicant's status.** Only HR actions do, with a reason, logged.
8. **AI provider is configurable (local | cloud)**. For now only **local** is wired and used; cloud stays implemented behind the same gateway, disabled until a key is provided.
9. **OCR is an off-the-shelf tool (PaddleOCR), not trained.** Provider is configurable (GPU model | CPU model | cloud | none).
10. **Names follow the client's requirements document**: AI Recruitment Settings, AI Job Profile, AI Job Criterion, AI Candidate Assessment, AI Assessment Evidence, AI Recruitment Job, AI Recruitment Audit Log; Job Opening fields `ai_enabled`, `ai_profile`, `ai_profile_approved`; Job Applicant fields `ai_status`, `ai_score`, `ai_assessment`, `ai_evaluated_on`.
11. **Scope.** Phase 1: client features 01–05 (job criteria, reading the application, screening/matching, ranking, HR review & decision). Phase 2: 10 (candidate comparison) and 13 (talent pool). **Postponed — do not build or stub:** AI interview questions, smart/voice interview, technical assessments, interview summary, job-offer draft, applicant status portal, recruitment dashboard.
12. **The client's 8 acceptance criteria** (in `docs/TESTING.md`) are the definition of done for phase 1.
13. **The engine owns the AI/OCR provider settings** (provider, model, OCR provider, timeout, retries). The Frappe screen *AI Recruitment Settings* reads them with `GET /v1/settings` and writes changes with `PUT /v1/settings`; the engine `.env` holds defaults only.
14. **An unreadable CV never fails a screening**: the screening continues from the form answers with flag `cv_unreadable`. `Failed` is reserved for engine errors (LLM, OCR, DB, timeout) after 3 attempts.
15. **Time**: the engine stores every timestamp in UTC; the local dev Frappe site runs on Asia/Riyadh.
16. **Web form**: the demo site has only the standard `job-application` form (discovery 2026-10-12). We add our own form and never assume a client-specific one exists.

## Hard rules for working on this server
- **The server is shared with colleagues.** Work only inside this project folder. Never stop, modify or remove containers, volumes, models, ports or files that are not ours.
- Docker Compose project name: **`talentai`**. All our containers, networks and volumes carry that prefix. Use host ports in the range **18000–18099** only, after checking they are free.
- **GPU is shared.** Before loading any model, run `nvidia-smi` and report free memory. Cap vLLM with `--gpu-memory-utilization` so we never take memory others are using. If another local LLM endpoint already exists on the server, tell Nadine before deciding to reuse it.
- **Ask Nadine before**: any `sudo` command, installing system packages, downloading models larger than 5 GB, opening ports outside the range, or touching anything outside this folder.
- **Never** connect to or modify `demo.hs1.ido.sa` or `secure4security.ido.sa` from code or scripts. Integration testing happens on our own local Frappe bench.
- **No real personal data.** Use synthetic applicants and CVs only. Never commit `.env`, keys, CV files, model weights or database dumps. `reference/` contains no credentials; keep it that way.
- **`~/my-projects/talent-ai-archive/`** holds Nadine's laptop copies (meeting recording, prompts, duplicates of `reference/`). Do not read it unless she asks.

## Working style
- Follow `docs/PLAN.md` phase by phase. **Stop at the end of every phase**, show Nadine what to test (in Egyptian Arabic, with exact commands/URLs), and wait for her OK before the next phase.
- Small commits on a feature branch per phase (`phase-1-core`, `phase-2-ocr`, …). Never push to `main` directly; Nadine merges.
- Every feature ships with tests. `make test` (engine) and the Frappe app tests must stay green.
- After each phase, update the **Status** section below (what is done, what is next, known issues).
- When something in this file or the docs is wrong or outdated, say so and propose the change; do not silently diverge.

## Repository layout (target)
```
talent-ai/                      <- this workspace = git repo 1 (github.com/123n-nadine/talent-ai, branch main)
  CLAUDE.md                     <- this file
  START.md                      <- first prompt used to kick off the work
  docs/                         <- ARCHITECTURE, PLAN, TESTING, DEPLOY_CHECKLIST, SERVER_REPORT, OPEN_QUESTIONS
  reference/                    <- client doc, clickable demo, discovery of the real system, Arabic guide (read-only)
  talent-engine/                <- the engine (part of repo 1)
  ido_talent_ai/                <- git repo 2 (github.com/123n-nadine/ido_talent_ai; repo root = app root so bench get-app works); git-ignored by repo 1
  dev-frappe/                   <- local Frappe dev bench (Docker); git-ignored, never committed
```

## Reference material (read when relevant)
- `reference/client-requirements/IDO Recruitment AI.docx` — the client's official requirements (Arabic). Source of names, features and acceptance tests.
- `reference/demo/talent-ai-demo.html` (+ `README.md`) — clickable prototype of the final UX. Open it in a browser. The Talent Console and the Frappe screens should behave like it. Its data is fictional.
- `reference/discovery/` — read-only discovery of the real demo system on 2026-10-12: versions, every DocType field, the public web form, data profile, gap analysis.
- `reference/guide/talent-ai-workflow.pdf` — Arabic step-by-step guide of the whole cycle.

## Status
- 2026-10-15: handoff prepared. Nothing built yet. Next: PLAN phase 0 (inspect the server and set up the workspace).
- 2026-10-15 (Phase 0 complete): server inspected read-only; findings, agreed GPU cap (0.40) and port table in `docs/SERVER_REPORT.md`. Nadine's decisions of 2026-10-15 applied to CLAUDE.md, ARCHITECTURE, PLAN, TESTING (decisions 13–16, `docs/OPEN_QUESTIONS.md`). Two repos on GitHub (`main`): `talent-ai` (this workspace incl. `talent-engine/`) and `ido_talent_ai`. `_laptop/` moved to `~/my-projects/talent-ai-archive/`. Nothing installed on the system, no sudo.
- 2026-10-15 (Phase 1 built, on branch `phase-1-core`, waiting for Nadine's check): engine core with the deterministic fake LLM and form answers only. FastAPI + RQ worker + Postgres/pgvector + Redis in compose project `talentai` (ports 18000/18030/18031), Alembic initial migration, all `/v1` endpoints of ARCHITECTURE §8 plus `/v1/settings`, `/v1/audit`, retry; scoring, eligibility, ranking groups, stale/duplicate detection, overrides, HMAC callback (verified end to end with `scripts/callback_receiver.py`). Seed = demo profile «مشرف أمن» + 26 synthetic applicants (`make seed`). 45 tests green, ruff + mypy clean.
- Known differences from the clickable demo in phase 1 (all expected): 2012 ranks 2nd (his CV contradiction appears in phase 2), 2013 is Completed (decision 14: no Failed for a corrupt CV), 2014 is Completed (the demo only froze him at Processing). RQ adds ~1.5 s overhead per job on top of ~0.5 s of pipeline time; to look at in phase 4 (time per 1000).
- 2026-10-15 (phase 1 merged into `main`; ports locked: DB/Redis on 127.0.0.1 only with a Redis password, API on 127.0.0.1 + Tailscale only, random secrets via `make env`, API key rotation on restart).
- 2026-10-15 (Phase 2 built, on branch `phase-2-ocr`, waiting for Nadine's check): CV upload with extraction (PyMuPDF with bidi row reconstruction, python-docx, LibreOffice, PaddleOCR CPU two-pass Arabic+English), redaction before any LLM step (regex + name hint + Presidio for Latin lines), `cv_unreadable` / `low_ocr_confidence` flags, `/v1/documents/inspect`, 20 synthetic CVs (`make cvs`), image with LibreOffice + Paddle (3.3 GB), 80 tests. Verified on the live stack: scanned Arabic CV read at 0.91 confidence with all personal data removed; corrupt CV → Completed with `cv_unreadable`; encrypted → unreadable.
- Known limits (phase 2): the Arabic OCR model loses digits inside Arabic sentences ("6 سنوات" → "سنوات"); OCR ~20 s per page on CPU; `paddle_vl` (GPU) is wired but untested until phase 3; `OCR_MIN_CONFIDENCE` 0.80 to be calibrated in phase 4; the CV is extracted and redacted only, the structured profile and quote evidence come in phase 3.
- 2026-10-15 (phase 2 merged into `main`).
- 2026-10-15 (Phase 3 built, on branch `phase-3-llm`, waiting for Nadine's check): vLLM service in the compose project (Qwen/Qwen3-8B-AWQ, fp16, 8192 ctx, cap 0.40, weights in the `talentai_models` volume, port internal only), one OpenAI-compatible client for `local` and `cloud` (cloud path proven with a mocked endpoint; switching is one settings call), prompts `profile-v1`/`judge-v1`/`draft-criteria-v1`, strict guided JSON, profile → evidence check in code (literal quotes, years from dates) → judgement (form level + CV level with quote) → verification. Live run on 26 synthetic applicants: 0 failures, mean 12.7 s per applicant (14.7 s with a CV), vLLM uses 8.65 GB of the GPU, 143/152 criteria with verified evidence, 70 confirmed by the CV. 89 tests.
- Known limits (phase 3): Turing has no FlashAttention (Triton backend, ~45 tok/s); the 8B model sometimes returns no form level for an answered question or a quote that is not in the text (5 of 152 criteria dropped as `quote_not_found`, 1 `evidence_mismatch`) and its rubric levels differ from the deterministic thresholds on some criteria (e.g. 2001 scores 92.5 instead of 100); PaddleOCR-VL on the GPU was not tried (needs a separate GPU image for Paddle); the CPU OCR stays the tested path.
- 2026-10-15 (phase 3 merged into `main`; OpenAI-compatible client approved instead of LiteLLM).
- 2026-10-15 (Phase 4 built, on branch `phase-4-eval`, waiting for Nadine's check): structured form answers are judged in code (model only for free text and the CV side; no model call when nothing needs it) → demo ranking identical to phase 1 again; tenant `judge_prompt` setting; gold set of 50 applicants (`talent-engine/eval/gold/GOLD_SET.md` for review); `eval/run.py` and `eval/bench.py`. Results in `docs/EVALUATION_REPORT.md`: Qwen3-8B-AWQ + `judge-v1` chosen (98% exact levels, 100% within one step, 100% evidence, 100% eligibility, rerun and name-swap 100%); `judge-v2` (Arabic) and Qwen3-4B-AWQ worse; 14B needs a higher cap (not downloaded). Throughput: 1000 applicants ≈ 55 min with 8 workers, 78 min with 4 (default), GPU ≤ 9.5 GB. 89 tests.
- 2026-10-15 (phase 4 merged into `main`; real-data labelling by the client's HR added to OPEN_QUESTIONS #13).
- 2026-10-15 (Phase 5 built, on branch `phase-5-console`, waiting for Nadine's check): Talent Console at `/console` (same port, 127.0.0.1 + Tailscale only), login with a signed HttpOnly cookie that `/v1` accepts for the default tenant (API key never in the browser, actions audited as `console:<user>`), all screens of PLAN phase 5 built on the real API, styled with the prototype stylesheet, Arabic RTL with an English toggle, developer view with the raw API calls, score disclaimer wherever a score appears. Criterion results now also store `form_level`, `cv_level` and the verified `cv_quote` (migration d4b2e3f6a7b8) so the CV panel highlights the quotes that confirm form answers. Render-tested every screen in headless Chrome (no JS errors, no overflow). LLM criteria drafts are normalised in code (slug keys, question links, five levels) so they can be approved as is. 96 tests.
- Known limits (phase 5): applicant names live only in the console's browser storage (engine never stores names), so seeded applicants show their reference; HR status buttons are left to Frappe (phase 6).
- Next: Nadine tests the console (steps in the phase-5 message), merges `phase-5-console`, then PLAN phase 6 (Frappe app on a local bench) on `phase-6-frappe`.
