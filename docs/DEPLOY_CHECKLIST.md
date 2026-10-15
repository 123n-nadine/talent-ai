# Rules that make the move to the real platform safe

Follow these from day one. The goal: after testing on our local bench, installing on the client platform is `bench get-app` + `install-app` + deploy the engine container + fill settings, with nothing else.

## While building

1. **Same versions.** Local bench uses the client versions from `reference/discovery/01_environment.md` (Frappe 16.31.x, ERPNext 16.32.x, HRMS develop at a pinned commit). Re-check the production versions before deploying; HRMS is on a development branch and can change.
2. **Everything as code.** Every DocType, Custom Field, Property Setter, Web Form, Role and Workspace change lives in the app (fixtures or JSON). Nothing done by hand in the UI that is not exported.
3. **Never edit platform code** (frappe, erpnext, hrms) or the client's existing web form. We add our own.
4. **Nothing hardcoded.** URLs, keys, model names, thresholds, ports come from AI Recruitment Settings or `.env`.
5. **Check before creating fields.** The client site may already have some fields; fixtures must not duplicate or rename them.
6. **Engine in Docker** with a pinned image, health checks and a volume for files and models.
7. **Migrations** (Alembic for the engine, Frappe patches for the app) for every schema change, never manual SQL.
8. **Uninstall is clean**: removing the app leaves the platform working.

## Before deploying (fill DEPLOY.md with the answers)

| item | question to answer | who |
|---|---|---|
| Versions | Production Frappe/ERPNext/HRMS versions and commit | Frappe team |
| Engine host | Where the engine runs (same server, another server in KSA, our GPU server) and is that location approved under PDPL | Abdullah + client |
| Network | Frappe → engine reachable (URL, TLS); engine → Frappe callback reachable | Frappe team / infra |
| Workers | Background workers running on the site (`long` queue) | Frappe team |
| Scheduler | Enabled or not (only affects automatic retries) | Frappe team |
| Files | Engine can receive CV files (sent by the app as multipart, so no direct file access needed) | us |
| API user | Dedicated Frappe user/API key with minimum permissions for the callback | Frappe team |
| Secrets | api_key and callback_secret set in AI Recruitment Settings, engine `.env` | us + Frappe team |
| GPU | GPU available where the engine runs, or CPU-only OCR + cloud LLM with written approval | infra + client |
| Backups | Engine DB backup and retention policy | infra |
| Rollback | Disable `ai_enabled` per job or `enabled` in settings; uninstall steps | us |

## Release steps (draft)

1. Freeze versions and tag both repos.
2. Deploy engine (compose) → `/ready` green → run the gold-set smoke test.
3. On a staging copy of the site: `bench get-app <repo> --branch <tag>`, `bench --site <site> install-app ido_talent_ai`, `bench --site <site> migrate`, restart workers.
4. Fill settings, create one job profile, run acceptance tests 1–6 and 8 with synthetic applicants.
5. Only then repeat on production, with `ai_enabled` off until HR approves the first profile.
