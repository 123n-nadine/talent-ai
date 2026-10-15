"""Throughput benchmark: N applicants (gold set repeated with new refs), measured wall time with the
current number of workers (`docker compose up -d --scale worker=K`). Samples GPU memory meanwhile.

Usage: uv run python -m eval.bench --n 100 --label w4
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv  # type: ignore[import-not-found]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval.run import cv_pdf, load_gold, wait  # noqa: E402

load_dotenv()
API = os.environ.get("API_URL", f"http://127.0.0.1:{os.environ.get('API_PORT', '18000')}")
KEY = os.environ.get("TENANT_API_KEY", "")
REPORTS = Path(__file__).resolve().parent / "reports"


def gpu_sampler(samples: list[int], stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            samples.append(int(out.stdout.strip().splitlines()[0]))
        except Exception:  # noqa: BLE001
            pass
        stop.wait(5)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--label", required=True)
    ap.add_argument("--workers", type=int, default=None, help="recorded in the report only")
    args = ap.parse_args()
    c = httpx.Client(
        base_url=API,
        headers={"Authorization": f"Bearer {KEY}", "X-Talent-Actor": "bench"},
        timeout=600,
    )
    jobs, apps = load_gold()
    for ref, job in jobs.items():
        c.put(f"/v1/jobs/{ref}", json=job).raise_for_status()
    # build N applicants by cycling the gold set under new refs (CV files rendered once per source)
    batch = []
    for i in range(args.n):
        src = apps[i % len(apps)]
        batch.append({**src, "ref": f"BENCH-{args.label}-{i:04d}", "src": src["ref"]})
    with tempfile.TemporaryDirectory(prefix="talentai-bench-") as tmp:
        pdfs: dict[str, Path] = {}
        for a in batch:
            if a.get("cv_lines") and a["src"] not in pdfs:
                pdfs[a["src"]] = cv_pdf(a["cv_lines"], Path(tmp), a["src"])
        print(
            f"prepared {len(batch)} applicants ({sum(1 for a in batch if a.get('cv_lines'))} with CV)"
        )
        samples: list[int] = []
        stop = threading.Event()
        threading.Thread(target=gpu_sampler, args=(samples, stop), daemon=True).start()
        t0 = time.time()
        ids = {}
        for a in batch:
            c.put(
                f"/v1/candidates/{a['ref']}", json={"facts": a["facts"], "answers": a["answers"]}
            ).raise_for_status()
            if a.get("cv_lines"):
                with open(pdfs[a["src"]], "rb") as fh:
                    c.put(
                        f"/v1/candidates/{a['ref']}/cv",
                        files={"file": (pdfs[a["src"]].name, fh)},
                        data={"name_hint": a["name_hint"]},
                    ).raise_for_status()
            r = c.post(
                "/v1/screenings",
                json={"job_ref": a["job"], "candidate_ref": a["ref"], "force": True},
            )
            ids[a["ref"]] = r.json()["screening_id"]
        t_submitted = time.time()
        results = wait(c, ids, timeout=7200)
        t_done = time.time()
        stop.set()
    done = [s for s in results.values() if s["status"] != "failed"]
    times = [s["versions"].get("total_ms", 0) / 1000 for s in done]
    report = {
        "label": args.label,
        "date": datetime.now(UTC).isoformat(),
        "n": args.n,
        "workers": args.workers,
        "with_cv": sum(1 for a in batch if a.get("cv_lines")),
        "submit_s": round(t_submitted - t0, 1),
        "processing_wall_s": round(t_done - t_submitted, 1),
        "total_wall_s": round(t_done - t0, 1),
        "failed": [r for r, s in results.items() if s["status"] == "failed"],
        "per_applicant_pipeline_mean_s": round(statistics.mean(times), 2) if times else None,
        "throughput_applicants_per_min": round(60 * len(done) / (t_done - t_submitted), 1),
        "projected_1000_min": round(1000 / (60 * len(done) / (t_done - t_submitted)), 1),
        "gpu_used_mib_max": max(samples) if samples else None,
        "gpu_used_mib_mean": int(statistics.mean(samples)) if samples else None,
    }
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"{datetime.now(UTC).strftime('%Y-%m-%d_%H%M')}-bench-{args.label}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
