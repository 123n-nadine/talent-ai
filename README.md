# Talent AI

AI screening and ranking layer for the recruitment module of a Frappe HRMS platform (i-do Holding). The AI reads each application, checks hard eligibility rules in code, judges HR-approved criteria with cited evidence, scores and ranks, and explains why. HR always makes the final decision.

This repository is the project workspace:

| Path | What |
|---|---|
| `CLAUDE.md` | Project memory and rules for Claude Code. Read first |
| `docs/` | ARCHITECTURE, PLAN (phases), TESTING, DEPLOY_CHECKLIST, SERVER_REPORT, OPEN_QUESTIONS |
| `reference/` | Client requirements, clickable demo, discovery of the demo site, Arabic guide (read-only) |
| `talent-engine/` | The standalone engine (FastAPI + worker + Postgres/pgvector + Redis + vLLM + PaddleOCR) with its Talent Console |
| `ido_talent_ai/` | **Separate repo** (`github.com/123n-nadine/ido_talent_ai`), git-ignored here: the Frappe app |
| `dev-frappe/` | Local Docker Frappe bench for testing the app; git-ignored |

Status and next step: see the **Status** section at the end of `CLAUDE.md`.
