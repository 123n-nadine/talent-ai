"""Run the gold set through the live engine and measure it against the expected levels.

Usage: uv run python -m eval.run --label 8b-v1 [--prompt judge-v1] [--repeat 2] [--name-swap]
Needs a running stack (API on API_URL) with the wanted model served by vLLM. Writes
eval/reports/<date>-<label>.json and .md (git-ignored).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv  # type: ignore[import-not-found]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.make_cvs import build_docx, docx_to_pdf  # noqa: E402

load_dotenv()
API = os.environ.get("API_URL", f"http://127.0.0.1:{os.environ.get('API_PORT', '18000')}")
KEY = os.environ.get("TENANT_API_KEY", "")
GOLD = Path(__file__).resolve().parent / "gold"
REPORTS = Path(__file__).resolve().parent / "reports"


def load_gold() -> tuple[dict, list[dict]]:
    jobs, apps = {}, []
    for f in ("security_supervisor.json", "data_analyst.json"):
        d = json.loads((GOLD / f).read_text())
        apps.extend(d["applicants"])
        jobs[d["applicants"][0]["job"]] = d["job"]
    return jobs, apps


def cv_pdf(lines: list[str], workdir: Path, ref: str) -> Path:
    docx = workdir / f"{ref}.docx"
    build_docx(docx, lines[0], lines[1:])
    return docx_to_pdf(docx, workdir)


def submit(
    c: httpx.Client, jobs: dict, apps: list[dict], workdir: Path, name_swap: bool, attach_cv: bool
) -> dict[str, str]:
    for ref, job in jobs.items():
        c.put(f"/v1/jobs/{ref}", json=job).raise_for_status()
    ids = {}
    for a in apps:
        c.put(
            f"/v1/candidates/{a['ref']}", json={"facts": a["facts"], "answers": a["answers"]}
        ).raise_for_status()
        if attach_cv and a.get("cv_lines"):
            hint = "سارة الخالد" if name_swap else a["name_hint"]  # same CV, different name hint
            lines = list(a["cv_lines"])
            if name_swap:
                lines = [ln.replace(a["name_hint"], hint) for ln in lines]
            pdf = cv_pdf(lines, workdir, a["ref"] + ("-swap" if name_swap else ""))
            with open(pdf, "rb") as fh:
                c.put(
                    f"/v1/candidates/{a['ref']}/cv",
                    files={"file": (pdf.name, fh)},
                    data={"name_hint": hint},
                ).raise_for_status()
        r = c.post(
            "/v1/screenings", json={"job_ref": a["job"], "candidate_ref": a["ref"], "force": True}
        )
        r.raise_for_status()
        ids[a["ref"]] = r.json()["screening_id"]
    return ids


def wait(c: httpx.Client, ids: dict[str, str], timeout: int = 3600) -> dict[str, dict]:
    out, deadline = {}, time.time() + timeout
    pending = set(ids)
    while pending and time.time() < deadline:
        for ref in list(pending):
            s = c.get(f"/v1/screenings/{ids[ref]}").json()
            if s["status"] not in ("queued", "processing"):
                out[ref] = s
                pending.discard(ref)
        if pending:
            time.sleep(2)
    return out


def model_judged_keys(job: dict) -> set[str]:
    """Criteria the language model levels from a free-text answer (every other structured answer
    is levelled in code from the rubric table)."""
    qtype = {q["key"]: q.get("type") for q in job.get("questions", [])}
    return {c["key"] for c in job["criteria"] if qtype.get(c.get("question")) == "text"}


def score(apps: list[dict], results: dict[str, dict], jobs: dict | None = None) -> dict:
    exact = within = total = 0
    evidence_ok = evidence_total = 0
    elig_ok = elig_total = 0
    flag_hits = flag_total = 0
    times, per_crit, failures = [], {}, []
    # round 6: the result split in two — what the code computes from the rubric table and what
    # the model judges (free text, and the CV side in the contradiction cases) — and how many
    # distinct texts the model was actually measured on
    split = {"code": {"exact": 0, "within": 0, "n": 0}, "model": {"exact": 0, "within": 0, "n": 0}}
    free_texts: set[str] = set()
    cv_docs = 0
    for a in apps:
        model_keys = model_judged_keys(jobs[a["job"]]) if jobs else set()
        if str(a.get("archetype", "")).startswith("contradiction"):
            model_keys = model_keys | {"supervision"}  # the expected level comes from the CV
        for k in model_judged_keys(jobs[a["job"]]) if jobs else set():
            q = next(c.get("question") for c in jobs[a["job"]]["criteria"] if c["key"] == k)
            if a["answers"].get(q):
                free_texts.add(a["answers"][q])
        cv_docs += bool(a.get("cv_lines"))
        s = results.get(a["ref"])
        if not s or s["status"] == "failed":
            failures.append(a["ref"])
            continue
        exp = a["expected"]
        elig_total += 1
        elig_ok += s["eligibility"] == exp["eligibility"]
        for f in exp.get("flags", []):
            flag_total += 1
            flag_hits += f in s["flags"]
        tol = exp.get("project_tolerance", 0)
        for c in s["criteria"]:
            e = exp["levels"].get(c["key"])
            if e is None:  # expected missing evidence
                ok = c["missing_evidence"]
                exact += ok
                within += ok
            else:
                got = c["effective_level"]
                is_exact = got == e
                is_within = abs(got - e) <= max(25, tol)
                exact += is_exact
                within += is_within
                d = per_crit.setdefault(c["key"], {"exact": 0, "within": 0, "n": 0})
                d["exact"] += is_exact
                d["within"] += is_within
                d["n"] += 1
                # a level taken from the CV (the model's reading overrode the form level) is the
                # model's judgement even when the criterion is a structured one
                by_model = c["key"] in model_keys or c.get("source") == "cv_quote"
                part = split["model" if by_model else "code"]
                part["exact"] += is_exact
                part["within"] += is_within
                part["n"] += 1
            total += 1
            if c["effective_level"] > 0 and not c["overridden_level"]:
                evidence_total += 1
                evidence_ok += bool(c["evidence"]) and not c["missing_evidence"]
        times.append(s["versions"].get("total_ms", 0) / 1000)
    return {
        "applicants": len(apps),
        "failed": failures,
        "level_exact": round(exact / total, 3) if total else None,
        "level_within_one_step": round(within / total, 3) if total else None,
        "levels_gt0_with_evidence": round(evidence_ok / evidence_total, 3)
        if evidence_total
        else None,
        "eligibility_correct": round(elig_ok / elig_total, 3) if elig_total else None,
        "expected_flags_found": round(flag_hits / flag_total, 3) if flag_total else None,
        "code_judged": {
            k: (round(v[k] / v["n"], 3) if v["n"] else None)
            for v in [split["code"]]
            for k in ("exact", "within")
        }
        | {"n": split["code"]["n"]},
        "model_judged": {
            k: (round(v[k] / v["n"], 3) if v["n"] else None)
            for v in [split["model"]]
            for k in ("exact", "within")
        }
        | {"n": split["model"]["n"]},
        "distinct_free_texts": len(free_texts),
        "cv_documents": cv_docs,
        "time_mean_s": round(statistics.mean(times), 2) if times else None,
        "time_median_s": round(statistics.median(times), 2) if times else None,
        "time_max_s": round(max(times), 2) if times else None,
        "per_criterion": {
            k: {
                "exact": round(v["exact"] / v["n"], 2),
                "within": round(v["within"] / v["n"], 2),
                "n": v["n"],
            }
            for k, v in per_crit.items()
        },
    }


def levels_of(results: dict[str, dict]) -> dict[str, dict[str, int]]:
    return {
        ref: {c["key"]: c["effective_level"] for c in s["criteria"]}
        for ref, s in results.items()
        if s["status"] != "failed"
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument(
        "--prompt", default=None, help="judge prompt to set on the tenant (judge-v1, judge-v2)"
    )
    ap.add_argument("--repeat", type=int, default=1, help="run N times to measure determinism")
    ap.add_argument(
        "--name-swap", action="store_true", help="also rerun the CVs with a different name hint"
    )
    ap.add_argument("--no-cv", action="store_true")
    args = ap.parse_args()
    c = httpx.Client(
        base_url=API,
        headers={"Authorization": f"Bearer {KEY}", "X-Talent-Actor": "eval"},
        timeout=600,
    )
    settings = c.get("/v1/settings").json()
    if args.prompt and settings.get("judge_prompt") != args.prompt:
        c.put("/v1/settings", json={"judge_prompt": args.prompt}).raise_for_status()
        settings = c.get("/v1/settings").json()
    jobs, apps = load_gold()
    report: dict = {
        "label": args.label,
        "date": datetime.now(UTC).isoformat(),
        "provider": settings["ai_provider"],
        "model": settings["ai_model"],
        "judge_prompt": settings.get("judge_prompt"),
        "runs": [],
    }
    runs_levels = []
    with tempfile.TemporaryDirectory(prefix="talentai-eval-") as tmp:
        for i in range(args.repeat):
            t0 = time.time()
            ids = submit(c, jobs, apps, Path(tmp), name_swap=False, attach_cv=not args.no_cv)
            results = wait(c, ids)
            wall = time.time() - t0
            m = score(apps, results, jobs)
            m["wall_s"] = round(wall, 1)
            report["runs"].append(m)
            runs_levels.append(levels_of(results))
            print(
                f"run {i + 1}: {json.dumps({k: v for k, v in m.items() if k != 'per_criterion'}, ensure_ascii=False)}"
            )
        if args.repeat > 1:
            same = sum(
                1
                for ref in runs_levels[0]
                if all(r.get(ref) == runs_levels[0][ref] for r in runs_levels[1:])
            )
            report["rerun_identical_applicants"] = round(same / len(runs_levels[0]), 3)
            print("rerun identical:", report["rerun_identical_applicants"])
        if args.name_swap and not args.no_cv:
            cv_apps = [a for a in apps if a.get("cv_lines")]
            ids = submit(c, jobs, cv_apps, Path(tmp), name_swap=True, attach_cv=True)
            swapped = levels_of(wait(c, ids))
            base = runs_levels[0]
            same = sum(1 for ref in swapped if swapped[ref] == base.get(ref))
            report["name_swap_identical_applicants"] = (
                round(same / len(swapped), 3) if swapped else None
            )
            print("name-swap identical:", report["name_swap_identical_applicants"])
    REPORTS.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
    (REPORTS / f"{stamp}-{args.label}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )
    m = report["runs"][0]
    md = [
        f"# Evaluation {args.label} ({stamp})",
        "",
        f"provider `{report['provider']}` · model `{report['model']}` · judge prompt `{report['judge_prompt']}`",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    for k in (
        "applicants",
        "failed",
        "level_exact",
        "level_within_one_step",
        "levels_gt0_with_evidence",
        "eligibility_correct",
        "expected_flags_found",
        "time_mean_s",
        "time_median_s",
        "time_max_s",
        "wall_s",
    ):
        md.append(f"| {k} | {m.get(k)} |")
    for k in ("rerun_identical_applicants", "name_swap_identical_applicants"):
        if k in report:
            md.append(f"| {k} | {report[k]} |")
    md += ["", "| part | exact | within one step | n |", "|---|---|---|---|"]
    for k, lab in (
        ("code_judged", "levelled in code from the rubric table"),
        ("model_judged", "judged by the model (free text, CV side)"),
    ):
        v = m.get(k) or {}
        md.append(f"| {lab} | {v.get('exact')} | {v.get('within')} | {v.get('n')} |")
    md.append(
        f"\ndistinct free texts the model was measured on: {m.get('distinct_free_texts')}; CV documents: {m.get('cv_documents')}"
    )
    md += ["", "| criterion | exact | within one step | n |", "|---|---|---|---|"]
    for k, v in m["per_criterion"].items():
        md.append(f"| {k} | {v['exact']} | {v['within']} | {v['n']} |")
    (REPORTS / f"{stamp}-{args.label}.md").write_text("\n".join(md) + "\n")
    print("report:", REPORTS / f"{stamp}-{args.label}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
