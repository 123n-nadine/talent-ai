# talent-engine

Standalone AI screening and ranking service for recruitment: reads each application (form answers first, CV optional), checks hard eligibility rules in code, judges HR-approved criteria with cited evidence, computes scores and ranks, and explains the result. HR always makes the final decision.

Host systems plug in through a small adapter over HTTP; the first adapter is the Frappe app `ido_talent_ai`. The engine ships with its own **Talent Console** web UI (phase 5) so the full cycle can be tested without any host system.

## Status

Phase 1 (engine core, fake LLM, form answers only) and phase 2 (documents: text extraction, PaddleOCR on CPU for scans, redaction before any LLM step) are implemented. Next phases: local LLM and structured CV profile (3), evaluation (4), console (5).

## Run (Docker Compose project `talentai`, host ports 18000–18099)

```bash
make env                      # once: writes .env with random secrets (chmod 600); never commit .env
make up                       # builds the image, starts db (18030), redis (18031), api (18000), worker
make cvs                      # 20 synthetic CV files into data/cvs (needs LibreOffice on the host; git-ignored)
make seed                     # demo profile "مشرف أمن" + 26 synthetic applicants (18 with a CV), prints the ranking
open http://127.0.0.1:18000/docs
```

Optional: receive the HMAC-signed callbacks locally

```bash
make receiver                 # listens on 18060
curl -X PUT http://127.0.0.1:18000/v1/settings -H "Authorization: Bearer $(grep ^TENANT_API_KEY .env | cut -d= -f2)" \
  -H 'Content-Type: application/json' \
  -d "{\"callback_url\":\"http://host.docker.internal:18060/callback\",\"callback_secret\":\"$(grep ^CALLBACK_SECRET .env | cut -d= -f2)\"}"
```

## Network and secrets

- Postgres and Redis are published on **127.0.0.1 only** (18030, 18031); Redis also requires a password. Nothing outside the server can reach them.
- The API is published on **127.0.0.1:18000 and on the Tailscale address only** (`API_BIND_TAILSCALE` in `.env`), never on `0.0.0.0` or the LAN.
- `make env` generates `TENANT_API_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` and `CALLBACK_SECRET`. To rotate the API key: change `TENANT_API_KEY` in `.env` and restart the api; the old key stops working immediately (audit event `tenant.key_rotated`).
- Postgres password changes need a fresh volume (`docker compose -p talentai down -v` removes only our volumes) or an `ALTER USER` inside the container.

## Documents and OCR

- Extraction: text PDF through PyMuPDF, DOCX through python-docx, DOC/RTF through LibreOffice headless, scanned PDF or image through the OCR provider. Corrupt, encrypted or unsupported files are recorded as `unreadable`; the screening then continues from the form answers with flag `cv_unreadable` (never Failed).
- OCR providers: `none`, `fake` (tests), `paddle_cpu` (PaddleOCR PP-OCRv5 server detector + Arabic mobile recogniser, CPU, oneDNN disabled because paddlepaddle 3.3 crashes with it), `paddle_vl` (GPU, phase 3). Models download on first use into the `models` volume (`PADDLE_PDX_CACHE_HOME`). First call takes ~30 s (model load), then a page takes a few seconds on 8 threads.
- Confidence: text-length-weighted mean of the recogniser scores; below `OCR_MIN_CONFIDENCE` (0.80 for now, to calibrate in phase 4) the screening is flagged `low_ocr_confidence` and goes to Needs Review.
- Redaction (before any LLM step): e-mails, URLs, Saudi mobiles and international numbers, national ID / iqama (10 digits starting 1 or 2), dates of birth and ages, nationality and gender words, addresses, the applicant's own name from `name_hint` (Arabic letter variants handled), plus English person names through Presidio + spaCy when installed. Arabic-Indic digits are normalised. The report counts what was removed; the engine never returns the raw text except through `inspect` with `include_raw`.

## Develop

```bash
uv sync                       # Python 3.12 venv in .venv (no system packages)
make test                     # pytest, SQLite in memory, inline queue, fake LLM
make lint typecheck           # ruff + mypy
make revision m="message"     # alembic autogenerate (needs the db container)
```

## Layout

```
app/api         FastAPI routers (jobs, candidates, screenings, settings, audit, health, console placeholder)
app/core        config, ids, time (UTC), Arabic normalisation, hashing, HMAC
app/domain      neutral contract (Pydantic) + Arabic labels
app/storage     SQLAlchemy models (ARCHITECTURE §7)
app/rules       hard eligibility rules (code only)
app/scoring     score / coverage / band / flags / strengths / gaps / raise-score
app/llm         provider contract, fake provider, templates; local/cloud arrive in phase 3
app/ocr         provider contract (phase 2)
app/pipeline    answers normalisation, evidence check, the 10-stage runner
app/services    jobs, candidates, screenings, ranking, settings, callback, audit, queue
app/worker      RQ worker
alembic/        migrations
scripts/        seed, callback receiver
tests/          pytest
```

## API in one minute

All `/v1/*` routes need `Authorization: Bearer <tenant key>`; optional `X-Talent-Actor: <user>` is recorded in the audit log.

| Route | Purpose |
|---|---|
| `PUT /v1/jobs/{ref}` | create/update a job; a new approved version only when the content changed; weights ≠ 100 → 422 |
| `POST /v1/jobs/draft-criteria` | draft criteria/rubric/questions (fake template in phase 1) |
| `GET /v1/jobs/{ref}/ranking` | ranked list + grouped others (not eligible, needs review, processing, failed, stale, duplicate) |
| `POST /v1/jobs/{ref}/rescreen` | rescreen every candidate against the active version |
| `PUT /v1/candidates/{ref}` | facts (allowed list only), answers, consent, `id_token` (HMAC of the national ID, computed by the host) |
| `DELETE /v1/candidates/{ref}` | full erasure |
| `PUT /v1/candidates/{ref}/cv` | multipart `file` (+ optional `name_hint`): store, extract (PDF/DOCX/DOC/RTF/JPG/PNG, OCR for scans), redact; the hint is used once and never stored. Changes the data hash, so earlier results become stale |
| `GET /v1/candidates/{ref}/cv`, `DELETE …/cv` | redacted text, method, OCR confidence, redaction counts / remove |
| `POST /v1/documents/inspect` | same processing without storing anything (`include_raw=true` also returns the raw text; synthetic data only) |
| `POST /v1/screenings` | screen candidate × job → 202; idempotent on the input hash unless `force` |
| `GET /v1/screenings/{id}` | full result with stages, evidence per criterion, rank |
| `POST /v1/screenings/{id}/override` | HR level override with a reason (recomputes) |
| `POST /v1/screenings/{id}/retry` | re-run a failed screening |
| `GET/PUT /v1/settings` | engine-owned provider/model/OCR values (decision 13) |
| `GET /v1/audit` | audit events |
| `GET /health`, `GET /ready` | liveness / readiness |

Callback: `POST {callback_url}` with `X-Talent-Signature: sha256=HMAC(secret, "<timestamp>.<body>")` and `X-Talent-Timestamp`; the receiver rejects a bad signature or a timestamp older than 5 minutes.
