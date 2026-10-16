"""Real numbers for the guide, read from the clean demo (Frappe API as the HR manager), the full
browser test (docs/test-run/full_test.json), the evaluation report and the open questions.
Nothing in the guide is typed by hand: every number comes from here.

    tools/.venv/bin/python tools/guide/facts.py     # writes docs/guide/facts.json
"""

from __future__ import annotations

import glob
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "ui"))
from pw import DEV, ENG  # noqa: E402

BASE = "http://127.0.0.1:18050"
ENGINE = "http://127.0.0.1:18000"
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"


class Frappe:
    def __init__(self, user: str, pw: str) -> None:
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.call("login", {"usr": user, "pwd": pw}, post=True)

    def call(self, method: str, args: dict | None = None, post: bool = False):
        url = f"{BASE}/api/method/{method}"
        data = None
        if post:
            data = json.dumps(args or {}).encode()
        elif args:
            url += "?" + urllib.parse.urlencode({k: v if isinstance(v, str) else json.dumps(v) for k, v in args.items()})
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "Accept": "application/json"})
        if post:
            csrf = next((c.value for c in self.jar if c.name == "csrf_token"), None)
            if csrf:
                req.add_header("X-Frappe-CSRF-Token", csrf)
        with self.op.open(req, timeout=120) as r:
            return json.loads(r.read() or b"{}").get("message")


def engine(path: str):
    req = urllib.request.Request(ENGINE + path, headers={"Authorization": f"Bearer {ENG['TENANT_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def parse_eval() -> dict:
    s = open(os.path.join(ROOT, "docs", "EVALUATION_REPORT.md"), encoding="utf-8").read()
    runs = {}
    for m in re.finditer(r"^\| (8B v1|8B v2|4B v1) \| `([^`]+)` \| `([^`]+)` \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+) s \|", s, re.M):
        runs[m.group(1)] = {"model": m.group(2), "prompt": m.group(3), "exact": float(m.group(4)), "within_one": float(m.group(5)),
                            "evidence": float(m.group(6)), "eligibility": float(m.group(7)), "flags": float(m.group(8)),
                            "free_text": float(m.group(9)), "supervision": float(m.group(10)), "seconds": float(m.group(11))}
    thr = {}
    for m in re.finditer(r"^\| (2|4|8) \| ([\d.]+) min \| ([\d.]+) \| (\d+) min \| (\d+) MiB \| (\d+) \|", s, re.M):
        thr[m.group(1)] = {"per100_min": float(m.group(2)), "per_min": float(m.group(3)), "per1000_min": int(m.group(4)), "gpu_mib": int(m.group(5)), "failures": int(m.group(6))}
    rerun = re.search(r"identical levels for \*\*(\d+)%\*\*", s)
    swap = re.search(r"Name-swap[^:]*: identical for \*\*(\d+)%\*\*", s)
    # the raw throughput reports (eval/bench.py): what the batch was made of and the measured times,
    # so the guide explains the thousand-applicant figure from the numbers themselves
    bench = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "talent-engine", "eval", "reports", "*-bench-*.json"))):
        r = json.load(open(p, encoding="utf-8"))
        bench[str(r["workers"])] = {"n": r["n"], "with_cv": r["with_cv"], "without_cv": r["n"] - r["with_cv"], "scanned": 0,  # the bench renders text PDFs only
                                   "pipeline_mean_s": r["per_applicant_pipeline_mean_s"], "submit_s": r["submit_s"], "processing_wall_s": r["processing_wall_s"],
                                   "total_wall_s": r["total_wall_s"], "per_min": r["throughput_applicants_per_min"], "projected_1000_min": r["projected_1000_min"],
                                   "failed": len(r["failed"])}
    return {"runs": runs, "throughput": thr, "bench": bench, "rerun_pct": int(rerun.group(1)) if rerun else None,
            "name_swap_pct": int(swap.group(1)) if swap else None, "gold": 50}


def parse_design() -> dict:
    """The design audit of TEST_REPORT §8: how many screens were measured and the count of every
    kind of issue before and after the design pass (the 10,487 of the bug table)."""
    s = open(os.path.join(ROOT, "docs", "TEST_REPORT.md"), encoding="utf-8").read()
    sec = s[s.index("## 8. Design pass"):] if "## 8. Design pass" in s else s
    issues = {m.group(1): {"before": int(m.group(2)), "after": int(m.group(3))} for m in re.finditer(r"^\| ([a-z-]+) \| (\d+) \| (\d+) \|", sec, re.M)}
    screens = re.search(r"(\d+) screens per run", sec)
    return {"screens": int(screens.group(1)) if screens else None, "issues": issues,
            "before": sum(v["before"] for v in issues.values()), "after": sum(v["after"] for v in issues.values())}


def parse_open_questions() -> dict:
    s = open(os.path.join(ROOT, "docs", "OPEN_QUESTIONS.md"), encoding="utf-8").read()
    open_part = s[: s.index("## Answered")] if "## Answered" in s else s
    rows = []
    for m in re.finditer(r"^\| (\d+) \| ([^|]+)\| ([^|]+)\| ([^|]+)\| ([^|]+)\|", open_part, re.M):
        rows.append({"n": m.group(1), "q": m.group(2).strip(), "who": m.group(3).strip(), "when": m.group(4).strip(), "state": m.group(5).strip()})
    return {"open": rows}


def main() -> None:
    hr = Frappe("hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])
    F: dict = {}
    rk = hr.call("ido_talent_ai.api.ranking", {"job_opening": OP1})
    F["ranking"] = {"title": rk.get("job_title"), "total": rk.get("total"), "applicants_total": rk.get("applicants_total"),
                    "ranked_total": rk.get("ranked_total"), "version": rk.get("job_version"),
                    "groups": {k: len(v) for k, v in rk["groups"].items()},
                    "top": [{"name": x.get("applicant_name"), "applicant": x.get("applicant"), "score": x.get("score"), "band": x.get("band"), "rank": x.get("rank"), "coverage": x.get("coverage")} for x in rk["ranked"][:6]],
                    "low": [{"name": x.get("applicant_name"), "score": x.get("score"), "band": x.get("band"), "rank": x.get("rank")} for x in rk["ranked"][-3:]],
                    "not_eligible": [{"name": x.get("applicant_name"), "reason": x.get("reason_ar")} for x in rk["groups"].get("not_eligible", [])]}
    d = hr.call("ido_talent_ai.api.get_assessment", {"applicant": "applicant.2002@example.com"})
    r = d["result"]
    crit_meta = {c["criterion_key"] if "criterion_key" in c else c.get("key"): c for c in d.get("criteria", [])}
    F["example"] = {
        "name": d["applicant_name"], "applicant": d["applicant"], "score": r["score"], "band": r["band"], "coverage": r["coverage"], "rank": r.get("rank"),
        "ranked_total": r.get("ranked_total"), "eligibility": r["eligibility"],
        "criteria": [{"key": c["key"], "text": c.get("text"), "weight": c.get("weight"), "level": c.get("effective_level", c.get("level")), "mandatory": c.get("mandatory"),
                      "source": c.get("source"), "evidence": (c.get("evidence") or "")[:120], "cv_quote": (c.get("cv_quote") or "")[:120],
                      "form_level": c.get("form_level"), "cv_level": c.get("cv_level")} for c in r["criteria"]],
        "stages": [{"key": s["key"], "label": s["label_ar"], "status": s["status"], "note": s.get("note"), "ms": s.get("ms")} for s in r.get("stages", [])],
        "cv": {k: (r.get("cv") or {}).get(k) for k in ("method", "ocr_confidence", "status", "pages", "chars")},
        "redaction": ((r.get("cv") or {}).get("redaction") or {}).get("counts"),
        "versions": r.get("versions"), "summary": r.get("summary"), "checks": r.get("eligibility_checks"),
        "strengths": r.get("strengths"), "weaknesses": r.get("weaknesses"), "raise": r.get("raise_score"),
    }
    F["profile"] = {"criteria": d.get("criteria"), "questions": d.get("questions")}
    for key, who in (("pdf", "applicant.2001@example.com"), ("word", "applicant.2018@example.com"), ("scan", "applicant.2002@example.com")):
        try:
            cva = hr.call("ido_talent_ai.api.cv_analysis", {"applicant": who})
            F.setdefault("cv_analysis", {})[key] = {"applicant": who, "method": cva.get("extraction_method"), "confidence": cva.get("ocr_confidence"),
                                                     "lines": len((cva.get("layout") or {}).get("lines", [])), "pages": len((cva.get("layout") or {}).get("pages", [])),
                                                     "chars": cva.get("chars"), "redaction": (cva.get("redaction") or {}).get("counts")}
        except Exception as e:  # noqa: BLE001
            F.setdefault("cv_analysis", {})[key] = {"error": str(e)}
    demo = json.load(open(os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai", "scripts", "demo_data.json"), encoding="utf-8"))
    mail = {a["key"][-4:]: a["email_id"] for a in demo["applicants"]}
    cases = {}
    for key, n in (("contradiction", "2012"), ("not_eligible", "2010"), ("blank", "2021"), ("blank_with_cv", "2009"), ("zero", "2006"), ("duplicate", "2016"),
                   ("corrupt", "2013"), ("nationality", "2011"), ("needs_review", "2021"), ("strong", "2001"), ("medium", "2004"), ("weak", "2005")):
        who = mail[n]
        a = hr.call("ido_talent_ai.api.get_assessment", {"applicant": who})
        res = a.get("result") or {}
        cases[key] = {"name": a.get("applicant_name"), "applicant": who, "score": res.get("score"), "band": res.get("band"), "eligibility": res.get("eligibility"),
                      "flags": res.get("flags"), "rank": res.get("rank"), "cv_note": a.get("cv_note"), "duplicate_of": a.get("duplicate_of"),
                      "duplicate_of_name": a.get("duplicate_of_name"),
                      "checks": [{"text": c.get("text_ar"), "ok": c.get("ok")} for c in res.get("eligibility_checks") or []],
                      "criteria": [{"key": c["key"], "text": c.get("text"), "level": c.get("effective_level", c.get("level")), "missing": c.get("missing_evidence"),
                                    "evidence": (c.get("evidence") or "")[:120], "contradiction": c.get("contradiction"), "form_level": c.get("form_level"),
                                    "cv_level": c.get("cv_level"), "cv_quote": (c.get("cv_quote") or "")[:120]} for c in res.get("criteria") or []]}
    F["cases"] = cases
    # consent defaults (OPEN_QUESTIONS #20, #21): the two paper applications and the withdrawn one
    con: dict = {"groups": {g: [{"name": x.get("applicant_name"), "applicant": x.get("applicant"), "at": x.get("at")} for x in rk["groups"].get(g, [])]
                            for g in ("awaiting_consent", "consent_withdrawn")}}
    paper = {a["key"][-4:]: a for a in demo.get("paper_applications", [])}
    con["paper_count"] = len(paper)
    for key, who in (("paper_waiting", paper["2026"]["email_id"]), ("paper_recorded", paper["2027"]["email_id"]), ("withdrawn", mail["2014"])):
        a = hr.call("ido_talent_ai.api.get_assessment", {"applicant": who})
        res = a.get("result") or {}
        con[key] = {"name": a.get("applicant_name"), "applicant": who, "ai_status": a.get("ai_status"), "consent": a.get("consent"),
                    "score": res.get("score"), "band": res.get("band"), "rank": res.get("rank"), "ranked_total": res.get("ranked_total")}
    ref = hr.call("frappe.client.get_value", {"doctype": "Job Applicant", "filters": mail["2014"], "fieldname": "ai_candidate_ref"})["ai_candidate_ref"]
    c = engine(f"/v1/candidates/{ref}")
    con["withdrawn"]["engine"] = {"consent": c.get("consent"), "facts": len(c.get("facts") or {}), "answers": len(c.get("answers") or {}),
                                  "documents": len(c.get("documents") or []), "screenings": len(c.get("screenings") or []),
                                  "withdrawn_from": c.get("withdrawn_from")}
    ev = engine(f"/v1/audit?ref={ref}")["events"]
    con["withdrawn"]["engine_audit"] = {"events": len(ev), "erased": sum(1 for e in ev if e["payload"] == {"erased": True}),
                                        "erasure": next((e["payload"] for e in ev if e["action"] == "candidate.consent_withdrawn"), {})}
    F["consent"] = con
    pool = hr.call("ido_talent_ai.api.talent_pool", {"job_opening": OP2})
    F["pool"] = {"suggestions": len(pool.get("suggestions", [])), "excluded": len(pool.get("excluded", [])),
                 "reasons": sorted({x.get("reason") for x in pool.get("excluded", [])}),
                 "top": [{"name": x.get("applicant_name"), "similarity": x.get("similarity")} for x in pool.get("suggestions", [])[:3]]}
    st = hr.call("ido_talent_ai.api.batch_status", {"job_opening": OP1})
    F["batch"] = st
    F["home"] = hr.call("ido_talent_ai.api.home_counts")
    F["settings"] = engine("/v1/settings")
    F["evaluation"] = parse_eval()
    F["design"] = parse_design()
    F["open_questions"] = parse_open_questions()
    ft = os.path.join(ROOT, "docs", "test-run", "full_test.json")
    if os.path.exists(ft):
        run = json.load(open(ft, encoding="utf-8"))
        F["tests"] = {"total": len(run["tests"]), "passed": sum(1 for t in run["tests"].values() if t["ok"]),
                      "items": {k: {kk: vv for kk, vv in v.items() if kk not in ("traceback",)} for k, v in run["tests"].items()},
                      "pages": run.get("timings", {}).get("pages", {}), "perm": run.get("perm", {})}
    out = os.path.join(ROOT, "docs", "guide", "facts.json")
    json.dump(F, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("facts:", ", ".join(F.keys()))


if __name__ == "__main__":
    main()
