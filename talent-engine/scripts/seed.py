"""Seed the running engine with the demo profile and synthetic applicants, then print the ranking.

Usage: uv run python scripts/seed.py  (reads API_URL and TENANT_API_KEY from .env / environment)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv  # type: ignore[import-not-found]

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.seed_data import CANDIDATES, JOBS  # noqa: E402

load_dotenv()
API = os.environ.get("API_URL", f"http://127.0.0.1:{os.environ.get('API_PORT', '18000')}")
KEY = os.environ.get("TENANT_API_KEY", "dev-talentai-key-change-me")
H = {"Authorization": f"Bearer {KEY}", "X-Talent-Actor": "seed-script"}


def main() -> int:
    c = httpx.Client(base_url=API, headers=H, timeout=300)
    r = c.get("/ready")
    print("ready:", r.status_code, r.json().get("ready"))
    for ref, job in JOBS.items():
        r = c.put(f"/v1/jobs/{ref}", json=job)
        r.raise_for_status()
        print(
            f"job {ref}: version {r.json()['version']['version']} (new={r.json()['new_version']})"
        )
    ids = []
    cv_dir = Path(os.environ.get("CV_DIR", Path(__file__).resolve().parent.parent / "data" / "cvs"))
    hints: dict[str, tuple[str, str]] = {}
    if (cv_dir / "name_hints.txt").exists():
        for line in (cv_dir / "name_hints.txt").read_text().splitlines():
            ref, fn, name = line.split("\t")
            hints[ref] = (fn, name)
    attached = 0
    for cand in CANDIDATES:
        body = {
            "id_token": cand["id_token"],
            "facts": cand["facts"],
            "answers": cand["answers"],
            "consent": True,
        }
        r = c.put(f"/v1/candidates/{cand['ref']}", json=body)
        r.raise_for_status()
        if cand["ref"] in hints:
            fn, name = hints[cand["ref"]]
            with open(cv_dir / fn, "rb") as fh:
                r = c.put(
                    f"/v1/candidates/{cand['ref']}/cv",
                    files={"file": (fn, fh)},
                    data={"name_hint": name},
                )
            r.raise_for_status()
            d = r.json()["document"]
            attached += 1
            conf = f" conf={d['ocr_confidence']}" if d.get("ocr_confidence") is not None else ""
            red = (d.get("redaction") or {}).get("counts")
            print(
                f"  cv {cand['ref']}: {d['status']} {d.get('extraction_method') or d.get('error')}{conf} chars={d['chars']} redacted={red}"
            )
        r = c.post(
            "/v1/screenings",
            json={
                "job_ref": cand["job"],
                "candidate_ref": cand["ref"],
                "force": os.environ.get("SEED_FORCE") == "1",
            },
        )
        r.raise_for_status()
        ids.append(r.json()["screening_id"])
    print(f"{len(ids)} screenings submitted ({attached} with a CV); waiting for the worker ...")
    deadline = time.time() + int(os.environ.get("SEED_WAIT_S", "900"))
    pending = set(ids)
    while pending and time.time() < deadline:
        for sid in list(pending):
            st = c.get(f"/v1/screenings/{sid}").json()["status"]
            if st not in ("queued", "processing"):
                pending.discard(sid)
        if pending:
            time.sleep(1)
    print("still pending:", len(pending))
    for ref in JOBS:
        rk = c.get(f"/v1/jobs/{ref}/ranking").json()
        print(
            f"\n=== {rk['job_title']} ({ref}) v{rk['job_version']}: {rk['ranked_total']} ranked of {rk['total']} ==="
        )
        for it in rk["ranked"]:
            print(
                f"  #{it['rank']:<2} {it['candidate_ref']}  score {it['score']:>5}  coverage {round((it['coverage'] or 0) * 100):>3}%  {it['band']}"
            )
        for g, items in rk["groups"].items():
            for it in items:
                print(f"  [{g}] {it['candidate_ref']}  score {it['score']}  {it['reason_ar']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
