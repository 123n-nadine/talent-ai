"""Independent check of docs/guide/COVERAGE.md: read the routes, DocTypes, endpoints and commands
straight from the code (not from the inventory) and report every one that COVERAGE.md misses, and
every row without a page, an existing screenshot or a test. Exit code 1 if anything is missing.

    python3 tools/guide/coverage_check.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP = os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai")
ENG = os.path.join(ROOT, "talent-engine")
COV = os.path.join(ROOT, "docs", "guide", "COVERAGE.md")


def from_code() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {"routes": [], "doctypes": [], "endpoints": [], "commands": []}
    for p in glob.glob(os.path.join(APP, "talent_ai", "page", "*", "*.json")):
        found["routes"].append("/desk/" + json.load(open(p, encoding="utf-8"))["page_name"])
    for p in glob.glob(os.path.join(APP, "www", "**", "*.html"), recursive=True):
        found["routes"].append("/" + os.path.relpath(p, os.path.join(APP, "www"))[:-5])
    js = open(os.path.join(ENG, "console", "static", "app.js"), encoding="utf-8").read()
    screens = re.search(r"const SCREENS = \{([^}]*)\}", js).group(1)
    found["routes"] += [f"Talent Console screen {k}" for k in re.findall(r"(\w+):r\w+", screens)]
    for p in glob.glob(os.path.join(APP, "talent_ai", "doctype", "*", "*.json")):
        j = json.load(open(p, encoding="utf-8"))
        if j.get("doctype") == "DocType":
            found["doctypes"].append(j["name"])
    for p in (os.path.join(APP, "api.py"), os.path.join(APP, "profile.py"), os.path.join(APP, "talent_ai", "doctype", "ai_recruitment_settings", "ai_recruitment_settings.py")):
        s = open(p, encoding="utf-8").read()
        mod = os.path.relpath(p, os.path.join(ROOT, "ido_talent_ai"))[:-3].replace("/", ".")
        found["endpoints"] += [f"/api/method/{mod}.{m}" for m in re.findall(r"@frappe\.whitelist\([^)]*\)\n(?:@[^\n]+\n)*def ([a-z_]+)\(", s)]
    for p in glob.glob(os.path.join(ENG, "app", "api", "routers", "*.py")):
        s = open(p, encoding="utf-8").read()
        pm = re.search(r'APIRouter\([^)]*prefix="([^"]*)"', s)
        prefix = pm.group(1) if pm else ""
        found["endpoints"] += [f"{m.upper()} {prefix}{path}" for m, path in re.findall(r'@router\.(get|post|put|delete|patch)\(\s*"([^"]*)"', s)]
    mk = open(os.path.join(ENG, "Makefile"), encoding="utf-8").read()
    found["commands"] += [f"make {t}" for t in re.findall(r"^([a-z][a-z0-9_-]*):", mk, re.M)]
    for pat in ("talent-engine/scripts/*.py", "talent-engine/scripts/*.sh", "dev-frappe/*.sh", "tools/ui/*.py", "tools/guide/*.py",
                "ido_talent_ai/ido_talent_ai/scripts/*.py", "talent-engine/eval/*.py"):
        found["commands"] += [os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, pat)) if not os.path.basename(f).startswith("__")]
    return found


def main() -> int:
    cov = open(COV, encoding="utf-8").read()
    rows = [r for r in cov.splitlines() if re.match(r"^\| [A-Z]{2}-\d{3} \|", r)]
    names = "\n".join(rows)
    missing = {k: [x for x in v if x not in names] for k, v in from_code().items()}
    bad_rows = []
    for r in rows:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))]  # an escaped \| belongs to the cell
        code, page, shot, test = cells[0], cells[3], cells[4], cells[5]
        m = re.search(r"\]\(([^)]+)\)", shot)
        if page in ("", "—") or not m or not os.path.exists(os.path.join(ROOT, "docs", "guide", m.group(1))) or not test:
            bad_rows.append(code)
    total = sum(len(v) for v in from_code().values())
    n_missing = sum(len(v) for v in missing.values())
    print(f"code: {total} routes/DocTypes/endpoints/commands read from the code; COVERAGE.md rows: {len(rows)}")
    for k, v in missing.items():
        print(f"  {k}: {len(v)} missing" + (": " + ", ".join(v[:10]) if v else ""))
    print(f"rows without page, screenshot or test: {len(bad_rows)}" + (": " + ", ".join(bad_rows[:20]) if bad_rows else ""))
    print(f"MISSING: {n_missing + len(bad_rows)}")
    return 1 if n_missing or bad_rows else 0


if __name__ == "__main__":
    sys.exit(main())
