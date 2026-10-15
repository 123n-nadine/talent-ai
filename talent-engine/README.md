# talent-engine

Standalone AI screening and ranking service for recruitment: reads each application (form answers first, CV optional), checks hard eligibility rules in code, judges HR-approved criteria with cited evidence, computes scores and ranks, and explains the result. HR always makes the final decision.

Host systems plug in through a small adapter over HTTP; the first adapter is the Frappe app `ido_talent_ai`. The engine ships with its own **Talent Console** web UI (phase 5) so the full cycle can be tested without any host system.

## Status

Phase 1 (engine core, fake LLM, form answers only) is implemented: API, worker, Postgres + pgvector, Redis, Alembic migrations, scoring/eligibility/ranking/stale/duplicate logic, HMAC callbacks, seed data copied from the clickable demo, 45 tests. Next phases: documents and OCR (2), local LLM (3), evaluation (4), console (5).

## Run (Docker Compose project `talentai`, host ports 18000–18099)

```bash
cp .env.example .env          # once; never commit .env
make up                       # builds the image, starts db (18030), redis (18031), api (18000), worker
make seed                     # demo profile "مشرف أمن" + 26 synthetic applicants, prints the ranking
open http://127.0.0.1:18000/docs
```

Optional: receive the HMAC-signed callbacks locally

```bash
make receiver                 # listens on 18060
curl -X PUT http://127.0.0.1:18000/v1/settings -H 'Authorization: Bearer dev-talentai-key-change-me' \
  -H 'Content-Type: application/json' \
  -d '{"callback_url":"http://host.docker.internal:18060/callback","callback_secret":"dev-callback-secret-change-me"}'
```

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
| `POST /v1/screenings` | screen candidate × job → 202; idempotent on the input hash unless `force` |
| `GET /v1/screenings/{id}` | full result with stages, evidence per criterion, rank |
| `POST /v1/screenings/{id}/override` | HR level override with a reason (recomputes) |
| `POST /v1/screenings/{id}/retry` | re-run a failed screening |
| `GET/PUT /v1/settings` | engine-owned provider/model/OCR values (decision 13) |
| `GET /v1/audit` | audit events |
| `GET /health`, `GET /ready` | liveness / readiness |

Callback: `POST {callback_url}` with `X-Talent-Signature: sha256=HMAC(secret, "<timestamp>.<body>")` and `X-Talent-Timestamp`; the receiver rejects a bad signature or a timestamp older than 5 minutes.
