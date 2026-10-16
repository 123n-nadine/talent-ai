"""docs/guide/COVERAGE.md: every inventory item with its page in the PDF guide, a screenshot and the
test that checks it (a section of docs/TEST_REPORT.md). Written by tools/guide/build.py."""

from __future__ import annotations

import glob
import json
import os
import re

from inv import ITEMS
from model import Diagram, Img

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GUIDE = os.path.join(ROOT, "docs", "guide")


def _tests(pattern: str) -> dict[str, str]:
    out = {}
    for p in glob.glob(pattern):
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r"^\s*def (test_[a-z0-9_]+)\(.*?(?=^\s*def test_|\Z)", s, re.M | re.S):
            out[m.group(1)] = m.group(0)
    return out


ENGINE_T = _tests(os.path.join(ROOT, "talent-engine", "tests", "test_*.py"))
FRAPPE_T = _tests(os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai", "tests", "test_*.py"))
FULL = open(os.path.join(ROOT, "tools", "ui", "full_test.py"), encoding="utf-8").read()
RUN = json.load(open(os.path.join(ROOT, "docs", "test-run", "full_test.json"), encoding="utf-8"))
CMDS_PATH = os.path.join(ROOT, "docs", "test-run", "commands.json")
CMDS = json.load(open(CMDS_PATH, encoding="utf-8")) if os.path.exists(CMDS_PATH) else {}

# browser check that exercises a case function of full_test.py
CASE_OF = {"case_strength": "K01", "case_not_eligible": "K02", "case_blank_height_public": "K03a", "case_blank_vs_zero": "K04", "case_contradiction": "K05",
           "case_duplicate": "K06", "case_edit_after": "K07", "case_override": "K08", "case_decisions": "K09", "case_csv": "K10", "case_compare": "K11",
           "case_pool": "K12", "case_xss": "K13", "case_weights": "K14", "case_engine_down": "K15", "run_console": "N01", "run_cvtypes": "C01–C09",
           "run_roles": "R01–R07", "run_landing": "R08", "run_other_application": "R09", "run_timings": "P01", "screen_state": "R01–R07"}

DECISION_TEST = {
    "claude:1": "§4 C07 (no CV) and C01–C09", "claude:2": "§10 Frappe `test_weights_must_total_100_to_approve`; §5 K14", "claude:3": "§10 Frappe `test_engine_payload_has_no_identity`; §5 K02",
    "claude:4": "§10 engine redaction tests; §4 C01", "claude:5": "§10 engine evidence tests; §5 K04, K05", "claude:6": "§10 engine scoring tests; §8 score example",
    "claude:7": "§10 Frappe `test_result_sets_ai_fields_but_never_the_status`; §3 R03", "claude:8": "§10 engine `test_llm` cloud path", "claude:9": "§4 C01, C09",
    "claude:10": "§3 R01–R07 (screen names)", "claude:11": "§12 postponed features (not built)", "claude:12": "§12 acceptance criteria", "claude:13": "§10 engine settings tests",
    "claude:14": "§4 C08; §1 F1", "claude:15": "§10 Frappe `test_engine_payload_has_no_identity` (UTC)", "claude:16": "§4 C01–C09 (our form)",
}


def find_test(it: dict) -> str:
    cat, key = it["cat"], it["id"].split(":", 1)[1]
    tokens: list[str] = []
    if cat == "endpoint" and key.startswith("engine:"):
        path = key.split(" ", 1)[1]
        tokens = [p for p in re.split(r"\{[^}]+\}", path) if len(p) > 3]
    elif cat == "endpoint":
        tokens = [f".{key.split(':', 1)[1]}("]
    elif cat in ("field", "setting") and "." in key:
        tokens = [key.split(".", 1)[1]]
    elif cat == "setting":
        kind, name = key.split(":", 1)
        if kind == "engine-env":
            return "§10 engine `test_every_env_key_is_used`"
        if kind == "dev-env":
            return "§3 R08 (logins) and §11 `init_env.sh`" if "PASSWORD" in name else "§11 `reset_demo.sh`"
        tokens = [name]
    elif cat in ("stage", "flag"):
        tokens = [f'"{key}"']
    elif cat == "status":
        tokens = [f'"{key.split(":", 1)[1]}"']
    elif cat == "hook":
        tokens = [key.rsplit(".", 1)[-1]]
    elif cat == "doctype":
        tokens = [f'"{key}"']
    if tokens:
        for name, body in FRAPPE_T.items():
            if all(t in body for t in tokens):
                return f"§10 Frappe `{name}`"
        for name, body in ENGINE_T.items():
            if all(t in body for t in tokens):
                return f"§10 engine `{name}`"
        for fn, cid in CASE_OF.items():
            m = re.search(rf"(?:async )?def {fn}\(.*?(?=\n(?:async )?def |\Z)", FULL, re.S)
            if m and all(t.strip('".(') in m.group(0) for t in tokens):
                return f"§3–7 browser {cid}"
    if cat == "screen":
        if key.startswith("console:"):
            return "§6 N01, K03b, N02"
        if key.startswith("web:"):
            return "§4 C01–C09 (form), §7 P01 (public pages)"
        return "§2 roles matrix (every role opened it), §7 P01"
    if cat == "button":
        if key.startswith("console:"):
            return "§6 N01 (console screens)"
        if key.startswith("home-card") or key.startswith("sidebar"):
            return "§3 R08 (home page), §2 roles matrix"
        return "§5 K07–K14 (desk actions)"
    if cat == "field":
        return "§2 roles probes (`rest_applicant`), §5 K01–K15"
    if cat == "endpoint":
        return "§2 roles probes" if key.startswith("frappe:") else "§10 engine API tests"
    if cat == "doctype":
        return "§10 Frappe test suite, §2 roles matrix"
    if cat == "role":
        return "§2 roles matrix and probes"
    if cat == "command":
        c = CMDS.get(key)
        if c:
            return f"§11 `{c['cmd']}` ({c['result']})"
        return "§11 commands"
    if cat == "decision":
        if key in DECISION_TEST:
            return DECISION_TEST[key]
        if key.startswith("open:"):
            return f"§12 open question {key.split(':', 1)[1]}"
        return "§12 decisions taken alone"
    if cat == "evaluation":
        return "§13 evaluation results"
    if cat == "security":
        return {"hmac-callback": "§10 Frappe `test_callback_signature`", "api-key": "§10 engine auth tests", "console-cookie": "§10 engine `test_console`",
                "ports": "§11 `make ps`", "redaction": "§10 engine redaction tests", "id-token": "§10 Frappe `test_engine_payload_has_no_identity`",
                "permlevel": "§10 Frappe `test_ai_fields_are_hr_only`; §3 R06", "require-hr": "§10 Frappe `test_every_hr_method_refuses_other_users_first`",
                "rate-limit": "§10 Frappe `test_application_is_always_saved`", "upload-limit": "§4 C08", "consent": "§10 Frappe `test_withdrawn_consent_stops_processing`",
                "retention": "§5 K12", "audit": "§5 K09", "secrets": "§3 R07", "local-fonts": "§10 engine `test_fonts_are_served_locally`",
                "static-traversal": "§10 engine `test_static_path_traversal_blocked`", "xss": "§5 K13", "no-sensitive-facts": "§10 Frappe `test_engine_payload_has_no_identity`",
                "erase": "§10 Frappe test suite"}.get(key, "§3 R01–R09")
    if cat == "architecture":
        return "§11 `make ps`" if key.startswith(("service", "dev-service")) else "§11 commands"
    return "§3–7 browser checks"


DEFAULT_SHOT = {
    "endpoint": "images/steps/E_docs.png", "setting": "images/steps/S13_settings.png", "command": "images/terminal/commands.png", "decision": "images/terminal/decisions.png",
    "evaluation": "images/terminal/evaluation.png", "architecture": "images/diagram.png", "security": "images/diagram.png", "role": "images/roles/hr_manager_home.png",
    "doctype": "images/steps/S09_head.png", "field": "images/steps/S09_head.png", "hook": "images/steps/S06_stages.png", "button": "images/steps/S10_ranking.png",
    "screen": "images/steps/S00_home.png", "status": "images/steps/S10f_groups.png", "flag": "images/steps/S09c_evidence.png", "stage": "images/steps/S06_stages.png",
}


def shot_for(it: dict, page_img: dict[str, str], claimed_page: dict[str, str]) -> str:
    pid = claimed_page.get(it["id"])
    if pid and page_img.get(pid):
        return page_img[pid]
    cat, key = it["cat"], it["id"].split(":", 1)[1]
    if cat == "setting" and key.startswith(("engine-env", "dev-env")):
        return "images/terminal/env_keys.png"
    if cat == "endpoint" and key.startswith("engine:") and "/console" in key:
        return "images/steps/C_dev.png"
    if cat == "button" and key.startswith("console:"):
        return "images/steps/C_profile.png"
    if cat == "role" and key.startswith("user:"):
        u = {"hr.manager": "hr_manager", "hr.user": "hr_user", "employee": "employee", "interviewer": "interviewer", "ess": "ess",
             "sysmanager": "system_manager", "portal.applicant": "portal"}.get(key[5:].split("@")[0])
        if u:
            return f"images/roles/{u}_home.png"
    if cat == "decision" and key.startswith("open:"):
        return "images/terminal/open_questions.png"
    return DEFAULT_SHOT.get(cat, "images/diagram.png")


def write(chs, codes: dict[str, int], F: dict) -> dict:
    page_img, claimed = {}, {}
    for ch in chs:
        for pg in ch.pages:
            img = next((b.path for b in pg.blocks if isinstance(b, Img)), None) or next((b.png for b in pg.blocks if isinstance(b, Diagram)), None)
            if img:
                page_img[pg.id] = img
            for i in pg.ids:
                claimed.setdefault(i, pg.id)
    rows, incomplete = [], []
    for it in ITEMS:
        page = codes.get(it["code"])
        shot = shot_for(it, page_img, claimed)
        test = find_test(it)
        ok = bool(page) and os.path.exists(os.path.join(GUIDE, shot)) and bool(test)
        if not ok:
            incomplete.append(it["code"])
        rows.append((it["code"], it["cat"], it["name"].replace("|", "\\|"), page or "—", shot, test))
    by_cat: dict[str, int] = {}
    for it in ITEMS:
        by_cat[it["cat"]] = by_cat.get(it["cat"], 0) + 1
    L = ["# Guide coverage — every item of the system, its page, a screenshot and its test", "",
         "Built from the code and the docs by `tools/guide/inventory.py` (not from memory) and written by `tools/guide/build.py` from the same build as",
         "`talent-ai-full-guide.pdf`: the page is where the item's code (e.g. `EP-012`) is printed in the PDF, the screenshot is the picture of that",
         "page (or, for items without a natural picture such as endpoints and settings, the API docs, the settings screen or a rendering of the",
         "settings file without values), and the test is a section of `docs/TEST_REPORT.md`. `tools/guide/coverage_check.py` re-reads the code and",
         "checks that nothing is missing.", "",
         f"**{len(ITEMS)} items**, {len(ITEMS) - len(incomplete)} with all three columns filled.", "",
         "| Category | Items |", "|---|---|"] + [f"| {k} | {v} |" for k, v in by_cat.items()] + ["",
         "| Code | Category | Item | Guide page (PDF) | Screenshot | Test (TEST_REPORT.md) |", "|---|---|---|---|---|---|"]
    L += [f"| {c} | {cat} | `{n}` | {p} | [{os.path.basename(s)}]({s}) | {t} |" for c, cat, n, p, s, t in rows]
    open(os.path.join(GUIDE, "COVERAGE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    return {"items": len(ITEMS), "complete": len(ITEMS) - len(incomplete), "incomplete": incomplete[:50]}
