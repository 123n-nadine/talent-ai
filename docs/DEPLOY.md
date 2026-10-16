# Deploying Talent AI on the client platform

Written for: the Frappe team and whoever runs the engine server. It turns `DEPLOY_CHECKLIST.md` into concrete steps. Everything was rehearsed on the local bench (`dev-frappe/`, Frappe v16.31.0, ERPNext v16.32.0, HRMS develop 640af1592a01) and on a fresh site; open points are marked **to confirm** and tracked in `OPEN_QUESTIONS.md`.

> **The local bench's database runs in memory (tmpfs) for testing only.** The server we tested on has a slow disk, so `dev-frappe/` keeps MariaDB in RAM with a backup every 2 hours. Production uses the platform's normal disk-based MariaDB and its normal backups; nothing in the app depends on the in-memory setup.

Nothing in the platform code changes: the app adds DocTypes, custom fields, hooks, pages and one public page. Uninstalling it leaves the platform as it was.

## 1. What gets installed

| Part | Where | What |
|---|---|---|
| `talent-engine` | Docker host (GPU for the local LLM, or CPU + cloud LLM) | api (FastAPI), workers (RQ), Postgres 16 + pgvector, Redis, vLLM (Qwen3-8B-AWQ), embed (Qwen3-Embedding-0.6B on CPU) |
| `ido_talent_ai` | the Frappe bench of the client | 11 DocTypes, custom fields on Job Opening and Job Applicant, public form `/ai-apply/new`, desk pages (`talent-ai`, `ai-ranking`, `ai-batch`, `ai-talent-pool`), Workspace Sidebar «Talent AI», Arabic translations |

Network: Frappe → engine `https://<engine>/v1/...` with a Bearer key; engine → Frappe `https://<site>/api/method/ido_talent_ai.api.receive_result` signed with HMAC-SHA256 (`X-Talent-Signature`, `X-Talent-Timestamp`, 5-minute window). No other traffic. The national ID never leaves Frappe (only an HMAC token), and the engine never receives names, e-mails, phones, photos or IDs.

## 2. Answers needed before go-live

| Item | Status | Notes |
|---|---|---|
| Production versions (Frappe / ERPNext / HRMS commit) | **to confirm** (OPEN_QUESTIONS #1) | Discovery 2026-10-12: Frappe 16.31.0, ERPNext 16.32.0, HRMS develop 17.0.0-dev. The app declares `frappe >=16,<18` and `required_apps = erpnext, hrms` |
| Engine host and PDPL location | **to confirm** (#4) | Synthetic data only until approved |
| Network and TLS both ways | **to confirm** | Engine URL in AI Recruitment Settings; callback URL = site URL + `/api/method/ido_talent_ai.api.receive_result` |
| Background workers (`long` and `short` queues) | **to confirm** (#2) | Required: every screening runs in a worker. Without workers applications are still saved, but stay «Processing» |
| Scheduler | **to confirm** (#2) | Disabled on the demo site. Only the safety nets need it (every 2 min: missed callbacks, missed jobs, the engine erasure of a consent withdrawn while the engine was down; hourly: retry engine outages). Without it HR uses «إعادة المحاولة» / «إعادة تقييم الكل», and a pending erasure waits for the next withdrawal call |
| API user for the callback | not needed | The callback is verified by its HMAC signature and runs as Administrator inside `receive_result` only. **to confirm** with the Frappe team whether they prefer a dedicated user (#8) |
| Secrets | us | Engine: `make env` (random). Frappe: callback secret and ID-token secret are generated at install; paste the engine key and the callback secret into the right places (§4) |
| GPU | **to confirm** | Local LLM needs ~9.5 GB GPU (cap 0.40 on a 24 GB card). Without GPU: `AI_PROVIDER=cloud` with written approval |
| MariaDB isolation | **to confirm** (#15) | MariaDB 11.8 snapshot isolation is handled (short transactions + retries); check the production version |
| Time zone | **to confirm** (#9) | Demo site: Africa/Cairo. The engine stores UTC; the app converts application times to UTC |
| Backups | infra | Engine: Postgres volume `talentai_pgdata` + files volume `talentai_files`. Frappe: normal site backups |
| Paper applications and consent withdrawal | default in force (#20, #21) | Defaults decided by Nadine on 2026-10-16 until the client confirms: no AI without consent («بانتظار الموافقة» until HR records it with its source); a withdrawal takes the applicant out of the ranking and erases the AI data in the engine and in Frappe, the application stays |
| Rollback | ready | Turn off «AI screening enabled» on an opening, or «Enabled» in AI Recruitment Settings: applications keep working without AI. Full removal: §6 |

## 3. Engine

```bash
git clone git@github.com:123n-nadine/talent-ai.git && cd talent-ai/talent-engine
git checkout <release tag>
make env                      # random keys in .env (chmod 600); never commit it
# edit .env: AI_PROVIDER=local (or cloud + CLOUD_LLM_API_KEY), OCR_PROVIDER=paddle_cpu,
#            EMBEDDING_PROVIDER=local, VLLM_GPU_MEMORY_UTILIZATION to the agreed cap,
#            ports/bind addresses for this host
nvidia-smi                    # free memory must cover the cap before vLLM starts
make up WORKERS=4             # builds the images, runs migrations, starts every service
curl -s http://127.0.0.1:18000/ready          # db, redis, llm, ocr all ok
uv run python -m eval.run --label smoke       # gold set on the new host: compare with EVALUATION_REPORT.md
```

The API must be reachable from the Frappe server only (reverse proxy with TLS). Database, Redis, vLLM and embed stay on the internal Docker network.

## 4. Frappe app

On a staging copy of the site first:

```bash
cd frappe-bench
bench get-app git@github.com:123n-nadine/ido_talent_ai.git --branch <release tag>
bench --site <site> install-app ido_talent_ai
bench --site <site> migrate
bench restart                  # or restart the workers / supervisor programs
```

Then, as System Manager, open **AI Recruitment Settings**:

1. Engine URL, Engine API Key (`TENANT_API_KEY` from the engine `.env`), request timeout.
2. Callback URL (leave empty to use the site URL) — the callback secret is generated at install; copy it to the engine by saving the settings once (the app pushes it through `PUT /v1/settings`).
3. Allowed facts (default: nationality, age, height_cm, weight_kg), retention days, consent version and Arabic consent text (**to confirm** with the client, #7).
4. Press «تحديث من المحرك»: provider, model, OCR, timeout and retries come from the engine (decision 13); the status panel must show the engine «جاهز».

Rate limit of the public form: 20 applications per IP per 10 minutes; change with `bench --site <site> set-config talent_ai_apply_limit <n>` (#16).

## 5. First opening (smoke test, synthetic data)

1. **AI Job Profile** → new → «نسخ من قالب المسمى الوظيفي» or «اقتراح معايير AI» → check rubric, weights 100%, rules, questions → «اعتماد» (v1).
2. **Job Opening** → «AI screening enabled» → choose the profile → save. «AI profile approved» turns on and the «Apply now» button of the job page points to `/ai-apply/new`.
3. Submit 2–3 synthetic applications from the public page; watch «متابعة المعالجة» and the applicant page update by themselves.
4. Run the acceptance checks 1–6 and 8 (`ACCEPTANCE_REPORT.md`) with synthetic applicants, then repeat on production with «AI screening enabled» off until HR approves the first real profile.

## 6. Uninstall

```bash
bench --site <site> uninstall-app ido_talent_ai --yes
```

`before_uninstall` removes the custom fields on Job Opening and Job Applicant and the permission-level-1 rows it added; the DocTypes and their data are removed by Frappe. Applications stay as normal Job Applicants with their standard fields. Rehearsed on a fresh site (§8). In the engine, `DELETE /v1/candidates/{ref}` and `DELETE /v1/jobs/{ref}` erase per applicant / opening; dropping the engine volumes erases everything.

## 7. Upgrading an installed version

Engine: `make build` then `make up WORKERS=4` (or `make migrate` and a restart of `api` and `worker`); the Alembic revisions add columns only (the latest, `b9f7e8a1c2d3`, adds `candidates.consent_withdrawn_at` and `withdrawn_from`). Frappe: `bench --site <site> migrate` (new custom fields «مصدر الموافقة», «سجّل الموافقة», «تاريخ حذف بيانات الذكاء الاصطناعي», the AI statuses «بانتظار الموافقة» and «سحب الموافقة», the AI job status «أُلغيت») and `bench restart`. Applications saved earlier without consent keep an empty AI status; their «تسجيل الموافقة» button works the same. After an upgrade of the extraction or the redaction, run `docker exec talentai-api-1 python -m scripts.reprocess_cvs` (report) and then `--apply`: every stored CV is re-extracted and re-redacted in place, the report counts what still looked like personal data before and after, and the host's «إعادة تقييم القديم والفاشل» re-scores the applicants whose text changed.

## 8. Rehearsal on a fresh site (local bench)

See `ACCEPTANCE_REPORT.md` §«Clean install» for the log: a separate bench cloned from the local one, `bench get-app` from the app's git repository, new site with ERPNext + HRMS, `install-app`, `migrate`, the app tests, `uninstall-app`, and a check that Job Applicant still works without the app.
