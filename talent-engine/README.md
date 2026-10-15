# talent-engine

Standalone AI screening and ranking service for recruitment: reads each application (form answers first, CV optional), checks hard eligibility rules in code, judges HR-approved criteria with cited evidence, computes scores and ranks, and explains the result. HR always makes the final decision.

Host systems plug in through a small adapter over HTTP; the first adapter is the Frappe app `ido_talent_ai`. The engine ships with its own **Talent Console** web UI so the full cycle can be tested without any host system.

Status: Phase 0 (workspace set up). Nothing runnable yet. Build order: `docs/PLAN.md` in the workspace.

## Planned layout

```
app/        api, core, domain, pipeline/stages, rules, scoring, llm, ocr, storage, worker
console/    Talent Console (Arabic RTL first)
prompts/    versioned prompt files
tests/      pytest
eval/       gold set and evaluation runs
```

## Stack (planned)

FastAPI, Redis/RQ worker, Postgres 16 + pgvector, vLLM (local LLM, GPU), PaddleOCR, Presidio, Docker Compose project `talentai`, host ports 18000–18099.

## Development

Python tooling through `uv`. Pre-commit hooks: `uv tool install pre-commit && pre-commit install`.
