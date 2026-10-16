"""Inventory of everything the guide must cover, read from the code and the docs (not from memory):
screens, pages and buttons (Frappe, console, public site), DocTypes and added fields, engine and
Frappe endpoints, stages, flags and statuses, settings (AI Recruitment Settings and .env), roles,
make commands and scripts, decisions, evaluation results, security measures, architecture.

    python3 tools/guide/inventory.py            # writes docs/guide/inventory.json

Each item: {"id", "cat", "name", "label_ar", "source"}. The guide generator and
tools/guide/coverage_check.py both use this file; coverage_check re-reads the code on its own."""

from __future__ import annotations

import ast
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP = os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai")
ENG = os.path.join(ROOT, "talent-engine")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT)


def read(p: str) -> str:
    return open(p, encoding="utf-8").read()


def line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 1


ITEMS: list[dict] = []


def add(cat: str, key: str, name: str, label_ar: str = "", source: str = "", **extra) -> None:
    iid = f"{cat}:{key}"
    if any(x["id"] == iid for x in ITEMS):
        return
    # the technical name is shown left to right (boxes «للفريق التقني», the appendix, COVERAGE.md): there
    # the Arabic «» would land on the wrong sides of an Arabic label, plain quotes look the same on both
    name = name.replace("«", '"').replace("»", '"')
    ITEMS.append({"id": iid, "cat": cat, "name": name, "label_ar": label_ar, "source": source, **extra})


def literal(text: str, name: str):
    """Value of a top-level assignment `NAME = <literal>` (or annotated) in a Python file."""
    tree = ast.parse(text)
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name:
                return ast.literal_eval(node.value)
    raise KeyError(name)


# ----------------------------------------------------------------------------- Frappe app
def frappe_pages() -> None:
    for d in sorted(glob.glob(os.path.join(APP, "talent_ai", "page", "*", "*.json"))):
        j = json.load(open(d, encoding="utf-8"))
        route = "/desk/" + j["page_name"]
        add("screen", f"desk:{j['page_name']}", f"Frappe page {route}", j.get("title", ""), rel(d), route=route, roles=[r["role"] for r in j.get("roles", [])])


def frappe_doctypes() -> None:
    for d in sorted(glob.glob(os.path.join(APP, "talent_ai", "doctype", "*", "*.json"))):
        j = json.load(open(d, encoding="utf-8"))
        if j.get("doctype") != "DocType":
            continue
        kind = "child table" if j.get("istable") else "single" if j.get("issingle") else "document"
        add("doctype", j["name"], j["name"], "", rel(d), kind=kind, fields=len([f for f in j["fields"] if f["fieldtype"] not in ("Section Break", "Column Break", "Tab Break")]))
        if not j.get("istable"):
            route = "/desk/" + j["name"].lower().replace(" ", "-")
            add("screen", f"form:{j['name']}", f"Frappe {'form' if j.get('issingle') else 'list and form'} {route}", "", rel(d), route=route)


def frappe_extended_screens() -> None:
    hooks = read(os.path.join(APP, "hooks.py"))
    for dt in re.findall(r'"([A-Z][A-Za-z ]+)": "public/js/[a-z_]+\.js"', hooks):
        add("screen", f"form:{dt}", f"Frappe form {dt} (extended by the app)", "", "ido_talent_ai/ido_talent_ai/hooks.py")
    if "doctype_list_js" in hooks:
        for dt in re.findall(r'doctype_list_js = \{"([^"]+)"', hooks):
            add("screen", f"list:{dt}", f"Frappe list {dt} (AI columns)", "", "ido_talent_ai/ido_talent_ai/hooks.py")
    sb = os.path.join(APP, "workspace_sidebar", "talent_ai.json")
    j = json.load(open(sb, encoding="utf-8"))
    add("screen", "workspace:Talent AI", "Workspace sidebar «Talent AI»", "", rel(sb))
    for it in j.get("items", []):
        if it.get("link_to"):
            add("button", f"sidebar:{it['label']}", f"Sidebar item {it['label']} → {it.get('link_type')} {it['link_to']}", "", rel(sb))
    ico = os.path.join(APP, "desktop_icon", "talent_ai.json")
    if os.path.exists(ico):
        add("screen", "desktop_icon:Talent AI", "Desktop icon «Talent AI»", "", rel(ico))


def frappe_www() -> None:
    for p in sorted(glob.glob(os.path.join(APP, "www", "**", "*.html"), recursive=True)):
        route = "/" + os.path.relpath(p, os.path.join(APP, "www")).replace(".html", "")
        add("screen", f"web:{route}", f"Public page {route}", "", rel(p), route=route)
    web_js = os.path.join(APP, "public", "js", "talent_ai_web.js")
    add("screen", "web:/jobs", "Public job list /jobs (HRMS page, Talent AI requirements added)", "", rel(web_js), route="/jobs")
    add("screen", "web:/jobs/<route>", "Public job page /jobs/<route> (HRMS page, Apply button to the AI form)", "", rel(web_js), route="/jobs/security/security-supervisor-riyadh")


LABEL = re.compile(r'(?:T\.t|t|__)\(\s*"([^"]+)"')


def frappe_buttons() -> None:
    files = glob.glob(os.path.join(APP, "public", "js", "*.js")) + glob.glob(os.path.join(APP, "talent_ai", "**", "*.js"), recursive=True)
    for p in sorted(files):
        s = read(p)
        for m in re.finditer(r'add_(?:custom|inner)_button\(\s*([^,]+?),', s):
            lab = LABEL.search(m.group(1))
            if lab:
                add("button", f"frappe:{lab.group(1)}", f"Frappe button «{lab.group(1)}»", lab.group(1), f"{rel(p)}:{line_of(s, m.group(0))}")
        for m in re.finditer(r'\["(Shortlisted|Hold|Rejected)", t\("([^"]+)"', s):
            add("button", f"frappe:{m.group(2)}", f"Frappe decision button «{m.group(2)}» ({m.group(1)})", m.group(2), f"{rel(p)}:{line_of(s, m.group(0))}")
        for m in re.finditer(r'data-tai="([a-z]+)"', s):
            add("button", f"frappe-action:{m.group(1)}", f"Frappe in-page action data-tai={m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    home = read(os.path.join(APP, "talent_ai", "page", "ai_recruitment", "ai_recruitment.js"))
    for m in re.finditer(r'\{ n: (\d+), icon: "[^"]*", ar: "([^"]+)"', home):
        add("button", f"home-card:{m.group(1)}", f"Home page card {m.group(1)} «{m.group(2)}»", m.group(2), rel(os.path.join(APP, "talent_ai", "page", "ai_recruitment", "ai_recruitment.js")))


def frappe_fields() -> None:
    p = os.path.join(APP, "setup", "install.py")
    s = read(p)
    body = s[s.index("def custom_fields()"):s.index("def _permissions()")]
    current = None
    for line in body.splitlines():
        m = re.match(r'\s*"(Job Opening|Job Applicant)": \[', line)
        if m:
            current = m.group(1)
        for f in re.finditer(r'_f\("([a-z_]+)", "([A-Za-z ]+)", "([^"]*)"', line):
            if f.group(2) in ("Section Break", "Column Break"):
                continue
            add("field", f"{current}.{f.group(1)}", f"{current}.{f.group(1)} ({f.group(2)})", f.group(3), f"{rel(p)}:{line_of(s, f.group(0))}", doctype=current)


def frappe_methods() -> None:
    for p in [os.path.join(APP, "api.py"), os.path.join(APP, "profile.py"), os.path.join(APP, "talent_ai", "doctype", "ai_recruitment_settings", "ai_recruitment_settings.py")]:
        s = read(p)
        mod = rel(p)[len("ido_talent_ai/"):-3].replace("/", ".")
        for m in re.finditer(r'@frappe\.whitelist\(([^)]*)\)\n(?:@[^\n]+\n)*def ([a-z_]+)\(', s):
            guest = "allow_guest=True" in m.group(1)
            add("endpoint", f"frappe:{m.group(2)}", f"/api/method/{mod}.{m.group(2)}", "", f"{rel(p)}:{line_of(s, m.group(0))}", guest=guest)


def frappe_hooks() -> None:
    p = os.path.join(APP, "hooks.py")
    s = read(p)
    for m in re.finditer(r'"(after_insert|on_update|on_trash|validate)": "([a-z_.]+)"', s):
        add("hook", m.group(2), f"doc event {m.group(1)} → {m.group(2)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    for m in re.finditer(r'"(ido_talent_ai\.screening\.[a-z_]+)"', s):
        add("hook", m.group(1), f"scheduled job {m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    if "on_session_creation" in s:
        add("hook", "on_session_creation", "login hook → «التوظيف الذكي» for HR roles", "", f"{rel(p)}:{line_of(s, 'on_session_creation')}")


# ----------------------------------------------------------------------------- engine
def engine_endpoints() -> None:
    for p in sorted(glob.glob(os.path.join(ENG, "app", "api", "routers", "*.py"))):
        s = read(p)
        m = re.search(r'APIRouter\(([^)]*)\)', s)
        prefix = ""
        if m:
            pm = re.search(r'prefix="([^"]*)"', m.group(1))
            prefix = pm.group(1) if pm else ""
        for r in re.finditer(r'@router\.(get|post|put|delete|patch)\(\s*"([^"]*)"', s):
            path = prefix + r.group(2)
            add("endpoint", f"engine:{r.group(1).upper()} {path}", f"{r.group(1).upper()} {path}", "", f"{rel(p)}:{line_of(s, r.group(0))}")


def engine_labels() -> None:
    p = os.path.join(ENG, "app", "domain", "labels.py")
    s = read(p)
    for key, ar, en in literal(s, "STAGES"):
        add("stage", key, f"stage {key} — {en}", ar, rel(p))
    for k, (ar, en) in literal(s, "FLAGS").items():
        add("flag", k, f"flag {k} — {en}", ar, rel(p))
    for k, v in literal(s, "AI_STATUS").items():
        add("status", f"screening:{k}", f"screening status {k} → ai_status {v}", "", rel(p))
    for k, (ar, en) in literal(s, "BANDS").items():
        add("status", f"band:{k}", f"band {k} — {en}", ar, rel(p))
    for k, (ar, en) in literal(s, "ELIGIBILITY").items():
        add("status", f"eligibility:{k}", f"eligibility {k} — {en}", ar, rel(p))
    for k, (ar, en) in literal(s, "GROUP_REASONS").items():
        add("status", f"group:{k}", f"ranking group {k} — {en}", ar, rel(p))
    api = read(os.path.join(APP, "api.py"))
    for st in literal(api, "DECISIONS") if "DECISIONS =" in api else []:
        add("status", f"decision:{st}", f"HR decision {st} (Job Applicant.status)", "", "ido_talent_ai/ido_talent_ai/api.py")
    j = json.load(open(os.path.join(APP, "talent_ai", "doctype", "ai_recruitment_job", "ai_recruitment_job.json"), encoding="utf-8"))
    for f in j["fields"]:
        if f["fieldname"] == "status":
            for o in [x for x in (f.get("options") or "").split("\n") if x]:
                add("status", f"ai_job:{o}", f"AI Recruitment Job status {o}", "", "ido_talent_ai/ido_talent_ai/talent_ai/doctype/ai_recruitment_job/ai_recruitment_job.json")


def settings() -> None:
    j = json.load(open(os.path.join(APP, "talent_ai", "doctype", "ai_recruitment_settings", "ai_recruitment_settings.json"), encoding="utf-8"))
    for f in j["fields"]:
        if f["fieldtype"] in ("Section Break", "Column Break", "Tab Break", "HTML"):
            continue
        add("setting", f"frappe:{f['fieldname']}", f"AI Recruitment Settings.{f['fieldname']} ({f['fieldtype']})", f.get("label", ""),
            "ido_talent_ai/ido_talent_ai/talent_ai/doctype/ai_recruitment_settings/ai_recruitment_settings.json")
    p = os.path.join(ENG, ".env.example")
    s = read(p)
    for m in re.finditer(r"^([A-Z][A-Z0-9_]*)=", s, re.M):
        add("setting", f"engine-env:{m.group(1)}", f"engine .env {m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    p = os.path.join(ROOT, "dev-frappe", ".env.example")
    s = read(p)
    for m in re.finditer(r"^([A-Z][A-Z0-9_]*)=", s, re.M):
        add("setting", f"dev-env:{m.group(1)}", f"dev bench .env {m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    add("setting", "site:talent_ai_apply_limit", "site config talent_ai_apply_limit (public form rate limit)", "", "ido_talent_ai/ido_talent_ai/api.py")


def roles() -> None:
    p = os.path.join(APP, "setup", "install.py")
    for r in literal(read(p), "AI_ROLES"):
        add("role", r, f"role {r} (AI fields at permission level 1)", "", rel(p))
    s = read(os.path.join(APP, "scripts", "seed_demo.py"))
    for email, (name, rs) in literal(s, "USERS").items():
        add("role", f"user:{email}", f"demo user {email} ({', '.join(rs) or 'Website User'})", name, "ido_talent_ai/ido_talent_ai/scripts/seed_demo.py")
    for r in ("Administrator", "Interviewer", "Employee", "Employee Self Service", "Guest", "Website User"):
        add("role", r, f"role {r}", "", "tools/ui/full_test.py")


def commands() -> None:
    p = os.path.join(ENG, "Makefile")
    s = read(p)
    for m in re.finditer(r"^([a-z][a-z0-9_-]*):", s, re.M):
        add("command", f"make:{m.group(1)}", f"make {m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    for pat in ("talent-engine/scripts/*.py", "talent-engine/scripts/*.sh", "dev-frappe/*.sh", "tools/ui/*.py", "tools/guide/*.py",
                "ido_talent_ai/ido_talent_ai/scripts/*.py", "talent-engine/eval/*.py"):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            if os.path.basename(f).startswith("__"):
                continue
            add("command", f"script:{rel(f)}", rel(f), "", rel(f))
    for c in ("bench get-app", "bench --site <site> install-app ido_talent_ai", "bench --site <site> migrate",
              "bench --site <site> run-tests --app ido_talent_ai", "bench --site <site> uninstall-app ido_talent_ai"):
        add("command", f"bench:{c}", c, "", "docs/DEPLOY.md")


def decisions() -> None:
    p = os.path.join(ROOT, "CLAUDE.md")
    s = read(p)
    block = s[s.index("## Decisions already made"):s.index("## Hard rules")]
    for m in re.finditer(r"^(\d+)\. \*\*([^*]+)\*\*", block, re.M):
        add("decision", f"claude:{m.group(1)}", f"CLAUDE.md decision {m.group(1)}: {m.group(2).strip()}", "", f"CLAUDE.md:{line_of(s, m.group(0))}")
    p = os.path.join(ROOT, "docs", "PROGRESS.md")
    s = read(p)
    for sec in re.finditer(r"^## (.+)$", s, re.M):
        start = sec.end()
        nxt = re.search(r"^## ", s[start:], re.M)
        part = s[start:start + nxt.start()] if nxt else s[start:]
        title = sec.group(1) if len(sec.group(1)) <= 40 else sec.group(1)[:40].rsplit(" ", 1)[0].rstrip(",;:—– ") + "…"
        for d in re.finditer(r"Decisions taken alone:\n((?:- .+\n?)+)", part):  # a section can have several parts
            for b in re.finditer(r"^- \*\*([^*]+)\*\*", d.group(1), re.M):
                add("decision", f"progress:{b.group(1).strip()[:60]}", f"PROGRESS.md ({title}): {b.group(1).strip()}", "", f"docs/PROGRESS.md:{line_of(s, b.group(0))}")
    p = os.path.join(ROOT, "docs", "OPEN_QUESTIONS.md")
    s = read(p)
    for m in re.finditer(r"^\| ([AQ]?\d+) \| ([^|]+)\|", s, re.M):
        add("decision", f"open:{m.group(1)}", f"OPEN_QUESTIONS #{m.group(1)}: {m.group(2).strip()[:90]}", "", f"docs/OPEN_QUESTIONS.md:{line_of(s, m.group(0))}")


def evaluation() -> None:
    p = os.path.join(ROOT, "docs", "EVALUATION_REPORT.md")
    s = read(p)
    for m in re.finditer(r"^\| (8B v1|8B v2|4B v1) \|", s, re.M):
        add("evaluation", f"run:{m.group(1)}", f"gold-set run {m.group(1)}", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    for m in re.finditer(r"^\| (2|4|8) \| ([\d.]+ min)", s, re.M):
        add("evaluation", f"throughput:{m.group(1)}", f"throughput with {m.group(1)} workers ({m.group(2)} per 100)", "", f"{rel(p)}:{line_of(s, m.group(0))}")
    for k, t in (("rerun", "Rerun"), ("name-swap", "Name-swap"), ("ocr-threshold", "OCR_MIN_CONFIDENCE"), ("quote-ratio", "fuzzy ratio")):
        if t in s:
            add("evaluation", k, f"evaluation: {k}", "", f"{rel(p)}:{line_of(s, t)}")


SECURITY = [
    ("hmac-callback", "engine → Frappe results signed with HMAC-SHA256 (timestamp + body)", "ido_talent_ai/ido_talent_ai/api.py", "def receive_result"),
    ("api-key", "Bearer API key per tenant on every /v1 call; key never in browser code", "talent-engine/app/api/deps.py", ""),
    ("console-cookie", "console login with a signed HttpOnly cookie (12 h)", "talent-engine/app/console/auth.py", ""),
    ("ports", "ports bound to 127.0.0.1 and the Tailscale address only; DB/Redis on 127.0.0.1", "talent-engine/docker-compose.yml", ""),
    ("redaction", "redaction before any LLM step (name, phone, e-mail, ID, dob, nationality, gender, address)", "talent-engine/app/pipeline/runner.py", ""),
    ("id-token", "raw national ID never leaves Frappe: id_token = HMAC-SHA256(national_id, secret)", "ido_talent_ai/ido_talent_ai/screening.py", ""),
    ("permlevel", "AI fields and identity at permission level 1 (HR roles only)", "ido_talent_ai/ido_talent_ai/setup/install.py", ""),
    ("require-hr", "every HR method refuses other users first (permanent test)", "ido_talent_ai/ido_talent_ai/utils.py", "def require_hr"),
    ("rate-limit", "public form rate limit per IP", "ido_talent_ai/ido_talent_ai/api.py", "rate_limit"),
    ("upload-limit", "CV size limit 10 MB and allowed extensions", "ido_talent_ai/ido_talent_ai/api.py", "MAX_CV_BYTES"),
    ("consent", "consent recorded with its version; withdrawal stops processing and deletes the pool profile", "ido_talent_ai/ido_talent_ai/api.py", "def withdraw_consent"),
    ("retention", "retention period for the talent pool", "talent-engine/app/services/talent_pool.py", ""),
    ("audit", "every AI action and HR decision in the audit log (with reason and actor)", "ido_talent_ai/ido_talent_ai/utils.py", "def audit"),
    ("secrets", "secrets in Password fields and .env files, never in git, logs, the guide or images", "dev-frappe/.gitignore", ""),
    ("local-fonts", "no third-party calls from the screens (fonts served locally)", "talent-engine/console/static/app.css", ""),
    ("static-traversal", "console static files: path traversal refused", "talent-engine/app/api/routers/console.py", "def static"),
    ("xss", "every applicant text escaped before display", "ido_talent_ai/ido_talent_ai/public/js/talent_ai.js", "T.esc"),
    ("no-sensitive-facts", "the LLM never sees nationality, gender, age, name, photo or IDs", "talent-engine/app/pipeline/runner.py", ""),
    ("erase", "deleting an applicant de-identifies the audit rows", "ido_talent_ai/ido_talent_ai/screening.py", "def on_applicant_trash"),
]

ARCHITECTURE = [
    ("repo:talent-ai", "repository talent-ai (workspace, docs, engine, dev bench scripts)", "CLAUDE.md"),
    ("repo:ido_talent_ai", "repository ido_talent_ai (Frappe app, bench get-app)", "CLAUDE.md"),
    ("install", "install on the platform: bench get-app → install-app → migrate → settings", "docs/DEPLOY.md"),
    ("uninstall", "uninstall leaves the platform as it was (custom fields and permission rows removed)", "ido_talent_ai/ido_talent_ai/setup/install.py"),
    ("adapter", "the engine is standalone; Frappe is the first adapter (HTTP + HMAC callback)", "docs/ARCHITECTURE.md"),
    ("tenant", "one tenant per host system (API key)", "docs/ARCHITECTURE.md"),
    ("gpu-cap", "vLLM capped at 40% of the shared GPU", "docs/SERVER_REPORT.md"),
    ("in-memory-db", "the dev Frappe database runs in memory, for testing only", "docs/DEPLOY.md"),
    ("builder", "Docker images built with the default builder only", "talent-engine/Makefile"),
]


def compose_services(path: str) -> list[str]:
    """Names under the top-level `services:` key of a compose file."""
    out, inside = [], False
    for line in read(path).splitlines():
        if re.match(r"^[A-Za-z]", line):
            inside = line.startswith("services:")
            continue
        m = re.match(r"^  ([a-z][a-z0-9_-]*):\s*$", line)
        if inside and m:
            out.append(m.group(1))
    return out


def security_and_architecture() -> None:
    for k, t, src, needle in SECURITY:
        p = os.path.join(ROOT, src)
        ln = line_of(read(p), needle) if needle and os.path.exists(p) else 1
        add("security", k, t, "", f"{src}:{ln}")
    for path, key, label in (("talent-engine/docker-compose.yml", "service", "engine service {} (compose project talentai)"),
                             ("dev-frappe/docker-compose.yml", "dev-service", "dev bench service {} (compose project talentai-frappe)")):
        for name in compose_services(os.path.join(ROOT, path)):
            add("architecture", f"{key}:{name}", label.format(name), "", f"{path}:{line_of(read(os.path.join(ROOT, path)), '  ' + name + ':')}")
    for k, t, src in ARCHITECTURE:
        add("architecture", k, t, "", src)


def console() -> None:
    p = os.path.join(ENG, "console", "static", "app.js")
    s = read(p)
    nav = s[s.index("const NAV = ["):s.index("];", s.index("const NAV = ["))]
    for m in re.finditer(r"k:'([a-z]+)', ar:'([^']+)'", nav):
        add("screen", f"console:{m.group(1)}", f"Talent Console screen {m.group(1)}", m.group(2), f"{rel(p)}:{line_of(s, m.group(0))}")
    for k, ar in (("processing", "المعالجة"), ("applicant", "شاشة المتقدم"), ("login", "تسجيل الدخول")):
        add("screen", f"console:{k}", f"Talent Console screen {k}", ar, rel(p))
    seen = set()
    for m in re.finditer(r'data-action="([a-zA-Z]+)"[^>]*>([^<$]{0,40})', s):
        a = m.group(1)
        if a in seen:
            continue
        seen.add(a)
        add("button", f"console:{a}", f"Talent Console action {a}", m.group(2).strip(), f"{rel(p)}:{line_of(s, m.group(0))}")


def main() -> None:
    frappe_pages()
    frappe_doctypes()
    frappe_extended_screens()
    frappe_www()
    console()
    frappe_buttons()
    frappe_fields()
    frappe_methods()
    frappe_hooks()
    engine_endpoints()
    engine_labels()
    settings()
    roles()
    commands()
    decisions()
    evaluation()
    security_and_architecture()
    out = os.path.join(ROOT, "docs", "guide", "inventory.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ITEMS, f, ensure_ascii=False, indent=1)
    by = {}
    for x in ITEMS:
        by[x["cat"]] = by.get(x["cat"], 0) + 1
    print(len(ITEMS), "items", json.dumps(by))


if __name__ == "__main__":
    main()
