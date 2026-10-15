# Server report (Phase 0, read-only inspection)

Date: 2026-10-15 12:30 UTC. Host: `ido`. Inspected as user `nadine`, no `sudo`, nothing installed, no images pulled.
One transient container (`docker run --rm`, image already on the host) was started for 2 seconds to verify GPU passthrough; nothing else was created or changed.

## 1. Machine

| Item | Value |
|---|---|
| OS / kernel | Ubuntu 24.04.5 LTS, Linux 6.8.0-139-generic, x86_64 |
| CPU | 2 × Intel Xeon Platinum 8173M @ 2.00 GHz, 28 cores/socket, 112 threads |
| RAM | 376 GiB total, ~363 GiB free, 8 GiB swap (unused) |
| Disk (this folder, `/`) | 915 GB, 172 GB used, **697 GB free** (`/var/lib/docker` is on the same partition) |
| Load average | ~10–12 (a colleague's face-recognition stack, see §4) |
| Time zone | Etc/UTC |
| Network | LAN 192.168.8.149; Tailscale 100.85.37.127 (tailnet `tailc4f5b0.ts.net`); IPv6 public |
| Other users | `awais`, `mohand`, `nadine` (all three in group `docker`: `mohand`, `nadine`; `awais` runs the Luna stack) |
| sudo | password required (not used) |

## 2. GPU

| Item | Value |
|---|---|
| GPU | 1 × **Quadro RTX 6000, 24 576 MiB**, Turing, compute capability **7.5** |
| Driver / CUDA | NVIDIA driver **595.84**, CUDA **13.2** (driver API). Host `nvcc` 12.0; `/usr/local/cuda-11.8` also present |
| Memory in use | **372 MiB used / 23 644 MiB free** at inspection time |
| Processes on the GPU | `Xorg` 82 MiB and `gnome-shell` 88 MiB (desktop, root); `python3 luna_video_agent/run.py` 164 MiB (user `awais`) |
| Persistence mode | off; Perf P2; 0 % utilisation |

Colleague GPU reservations: the Luna compose project (`/var/lib/luna/current/example-docker/docker-compose.gpu.yml`) reserves the GPU (`count: all`) for two services, `remote-sdk` and `video-agent`. Both were restarting / "health: starting" during the inspection, so their steady-state memory is **unknown**; today they used < 200 MiB. Two stopped Docker volumes named `*-ollama-data` show Ollama was used on this host before; no LLM server is running now (no listener on 11434 / 8000).

Implications for us (Turing, sm_75):
- Use **AWQ or GPTQ int4 weights with fp16 compute**. No bf16, no FP8, no Marlin kernels, no FlashAttention-2 → vLLM will fall back to its Turing-compatible attention backend; expect lower throughput than on Ampere+. To be measured in Phase 3/4.
- Driver 595 runs any CUDA 12.x container image (backward compatible). We do not need the host CUDA toolkit.

### Recommended GPU memory cap

| Option | `--gpu-memory-utilization` | vLLM budget | Fits | Leaves for colleagues |
|---|---|---|---|---|
| **A (recommended start)** | **0.40** | ~9.8 GB | Qwen3-8B-AWQ (~5.6 GB weights) + ~3.5 GB KV cache (≈ 24k cached tokens, enough for 3–4 concurrent 6k-token screenings) | ~14 GB |
| B (if `awais` confirms Luna needs < 6 GB) | 0.50 | ~12.3 GB | same model, larger batch; or Qwen3-14B-AWQ with a short context | ~12 GB |
| C (ARCHITECTURE default) | 0.35 | ~8.6 GB | Qwen3-8B-AWQ with ~2.5 GB KV cache (tight, smaller batches) | ~15 GB |

Rules we will apply regardless of the option: run `nvidia-smi` before every model start; vLLM refuses to start if the requested share is not free; embedding model (Qwen3-Embedding-0.6B, ~1.2 GB) runs on CPU by default; PaddleOCR starts as `paddle_cpu`; the GPU OCR variant only after measuring. Downloading Qwen3-8B-AWQ (~5.6 GB) is above the 5 GB rule and needs Nadine's OK in Phase 3.

## 3. Docker

| Item | Value |
|---|---|
| Docker Engine | 29.1.3 (Ubuntu package), storage `overlayfs`, cgroup v2, root `/var/lib/docker` |
| Docker Compose | v5.5.1 (plugin). Legacy `docker-compose` binary absent |
| User in `docker` group | **yes** (`nadine`), no sudo needed |
| NVIDIA Container Toolkit | 1.20.1 installed; `nvidia` runtime registered in `/etc/docker/daemon.json` (default runtime is `runc`); CDI specs present (`nvidia.com/gpu=all`) |
| GPU passthrough test | `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` → **works** (saw the Quadro RTX 6000) |
| Bridge networks | 14 networks exist (172.17–172.28 in use). Default address pools still have room; if a compose project ever fails with "no available network", that is the cause (needs `sudo` to change `default-address-pools`, not needed now) |
| `docker system df` | took > 2 minutes (daemon busy with restarting containers). Result: images 42 (87.4 GB, 28 active), containers 29, volumes 31 (33.3 GB, only 1 attached to a running container), build cache 1.8 GB. All of it belongs to colleagues or to stopped projects; we never prune on this host |

Compose project names already taken: `example-docker` (Luna). `talentai` and `talentai-frappe` are free.

## 4. What colleagues run (names, images, ports only; not ours, never touch)

Running (project `example-docker`, VisionLabs **Luna** face-recognition platform, user `awais`, most services on `network_mode: host`):
`luna-api`, `luna-admin`, `luna-faces`, `luna-events`, `luna-handlers`, `luna-tasks`, `luna-tasks-worker`, `luna-sender`, `luna-streams`, `luna-video-agent`, `luna-video-manager`, `luna-accounts`, `luna-licenses`, `luna-image-store`, `luna-configurator`, `luna-remote-sdk`, `luna-python-matcher`, `luna-agent-bags`, `luna-agent-scanner`, `facestream`, `postgres` (postgis 16-3.5), `redis` (8.6), `influxdb` (2.9.1), plus `example-docker-{luna_point_ui,clementine_api,clementine_auth,point_api,vlnotifier,db}-1`. About half were in a restart loop during the inspection.

Host ports they occupy: **22, 53, 631, 3189, 3350, 3389 (xrdp), 5000, 5010, 5070, 5230, 5240, 5432 (Postgres), 6379 (Redis), 7070, 8080 (Luna UI), 8086 (InfluxDB)**, plus VS Code server ports (18866, 34407, 38029, 40923 on 127.0.0.1) and 34569, 35075, 37705.

Existing Postgres/Redis on 5432/6379 belong to Luna (host network). **We run our own Postgres and Redis inside the `talentai` compose project** and do not reuse theirs.

Stopped projects (volumes only, no containers, no images): `aiasst-*` (mariadb, ollama, pg), `sdf-*` (gitea, mariadb, ollama, pg), `erptest-*` (a Frappe bench: dbdata, sites, redis-queue, logs), `miyar_mariadb-data`, `viariyad-*`, `obs-*` (prometheus, jaeger, …). No Frappe/ERPNext/MariaDB images are present on the host any more.

## 5. Ports

Range **18000–18099: all free** (verified with `ss -ltn`). Proposed allocation (host side; container-internal ports stay default):

| Host port | Service | Exposed to host? |
|---|---|---|
| 18000 | talent-engine API (FastAPI) + Talent Console under `/console` | yes |
| 18010 | spare (the console is served under `/console` on 18000, decided 2026-10-15) | — |
| 18020 | vLLM OpenAI-compatible API | optional, for debugging only |
| 18030 | engine Postgres | optional, 127.0.0.1 only |
| 18031 | engine Redis | optional, 127.0.0.1 only |
| 18040 | Langfuse (later, optional) | yes |
| 18050–18059 | dev-frappe bench (18050 site HTTP, 18051 socketio, 18052 MariaDB 127.0.0.1) | yes |
| 18060 | local HMAC callback receiver used by tests | 127.0.0.1 only |
| 18070–18099 | spare | — |

Access from Nadine's laptop: VS Code port forwarding, or Tailscale `http://100.85.37.127:18000`, or LAN `http://192.168.8.149:18000`.

## 6. Languages and tools

| Tool | Status |
|---|---|
| Python | system `python3` **3.12.3** (`/usr/bin/python3`) **without `pip`, `venv` or `ensurepip`** (`python3-venv` not installed). `uv` **0.12.5** in `~/.local/bin` with a uv-managed **Python 3.12.14** → use `uv` for every venv/lock; no sudo needed |
| pip / pipx / conda | none |
| Node | **24.21.0**, npm 11.19.0 (via nvm) |
| git | 2.43.0. `~/.gitconfig` has **no `user.name` / `user.email`** (only a `safe.directory` entry) → needed before the first commit |
| make, jq, curl, wget, tmux, htop | present. `gh`, `nvtop`, `pre-commit`, `ruff`, `mypy`, `pytest` absent (install per-user with `uv tool install`, no sudo) |
| LibreOffice | `/usr/bin/soffice` present on the host (we will still use it inside the engine container for DOC/RTF) |
| Tesseract | absent (not needed; OCR is PaddleOCR in the container) |
| ulimit -n / inotify watches | 1 048 576 / 65 536 |

## 7. Frappe on this host

- `bench` is not on PATH; no `frappe-bench` under `/opt`.
- Nadine's earlier project `~/my-projects/منصه معيار erp/development/frappe-bench` contains **frappe 16.33.1 + erpnext 16.34.2 + miyar** (no hrms, no `env/`, site `miyar-dev.local`); it was run through Docker (volumes `erptest-*`, `miyar_*` remain, images removed). Not reusable for our client versions (Frappe 16.31.0 / ERPNext 16.32.0 / HRMS 17.0.0-dev). Our `dev-frappe/` bench in Phase 6 will be separate (project `talentai-frappe`, ports 18050–18059) and will need Frappe images (~2–3 GB) pulled after an OK.
- `~/software-development-factory/Frappe Arc` holds only design documents.

## 8. Outbound network (HEAD requests, no downloads)

| Target | Result |
|---|---|
| pypi.org, files.pythonhosted.org | reachable (200 / 404 on root as expected) |
| download.pytorch.org/whl | 200 |
| github.com | 200 |
| huggingface.co + model CDN (`us.aws.cdn.hf.co` xet bridge) | 200, redirects followed |
| Docker Hub (`registry-1.docker.io` 401 anonymous as expected; `auth.docker.io` token 200) | pulls will work |
| ghcr.io, nvcr.io, quay.io | reachable |
| paddleocr.bj.bcebos.com (PaddleOCR models) | 200 |
| archive.ubuntu.com, deb.debian.org | 200 |
| Proxy | none configured |

## 9. Workspace hygiene

- `reference/` contains no credentials (grep for password/api_key/secret/token hit only the sentence "`User.api_key` empty" in the discovery notes).
- `_laptop/` (85 MB: byte-identical copies of `reference/`, the prompt files used to build the demo, Playwright console logs and a meeting recording) was **moved on 2026-10-15 to `~/my-projects/talent-ai-archive/` (chmod 700)** on Nadine's instruction. It is outside the repo and is not read unless she asks.

## 10. Recommendation summary

1. **Docker, yes.** Everything (engine, worker, Postgres+pgvector, Redis, vLLM, PaddleOCR, later the dev bench) runs in Docker Compose project `talentai`; no system packages needed. Python tooling via `uv`; no sudo for Phases 0–7 as far as we can see.
2. **GPU cap: option A, `VLLM_GPU_MEMORY_UTILIZATION=0.40`** (~9.8 GB) with Qwen3-8B-AWQ, `--dtype float16`, `--max-model-len 8192` as the Phase 3 starting point; revisit after asking `awais` how much GPU the Luna `remote-sdk`/`video-agent` need when healthy. Fallback 0.35. **Approved by Nadine 2026-10-15**; she asks awais before Phase 3.
3. **Ports** as in §5; nothing in 18000–18099 is used today.
4. **Needs `sudo` (listed, not run, none required now):** none for the plan. Optional only: `apt install python3-venv python3-pip nvtop`; enlarging Docker `default-address-pools` if bridge networks run out; opening firewall ports if a colleague's laptop (not on Tailscale/LAN) must reach the console.
5. **Git identity and remotes (decided 2026-10-15):** repo-local `user.name`/`user.email` in each repo; remotes `git@github.com:123n-nadine/talent-ai.git` (workspace + engine) and `git@github.com:123n-nadine/ido_talent_ai.git`. SSH: `~/.ssh/id_ed25519_github` and a `github.com` entry in `~/.ssh/config` already existed, but GitHub refused the key at inspection time (not registered on the account); the existing key is kept and must be added to GitHub.
