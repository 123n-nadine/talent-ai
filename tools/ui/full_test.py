"""Round 2 full browser test of Talent AI on the local bench: every recruitment role, every CV type,
the special cases, timings and screenshots, in the server's Chrome through Playwright.

    tools/.venv/bin/python tools/ui/full_test.py [section ...]
    sections: roles cvtypes cases console timings   (default: all, in that order)

Results go to docs/test-run/full_test.json (tools/ui/test_report.py turns them into
docs/TEST_REPORT.md); screenshots to docs/guide/images/roles/ and docs/guide/images/test/ as
8-bit PNG. The run changes the demo data (new applications, decisions, profile v2, an engine
outage): run dev-frappe/reset_demo.sh afterwards. Synthetic data only. Passwords are read from
the .env files and never printed or saved."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import time
import traceback
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw import (  # noqa: E402
    BASE, CONSOLE, DEV, ENG, ROOT, browser, call_status, compact_png, login_console, new_page, settle, shot,
    wait_value, xcall,
)

DOCS = os.path.join(ROOT, "docs")
IMG = os.path.join(DOCS, "guide", "images")
OUT = os.path.join(DOCS, "test-run", "full_test.json")
SCRATCH = os.environ.get("TAI_SCRATCH", "/tmp/talentai-full-test")
CVS = os.path.join(ROOT, "talent-engine", "data", "cvs")
TEST_CVS = os.path.join(CVS, "test")
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"
A = lambda n: f"applicant.{n}@example.com"  # noqa: E731
DATA = json.load(open(os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai", "scripts", "demo_data.json"), encoding="utf-8"))
SECTIONS = sys.argv[1:] or ["roles", "cvtypes", "cases", "console", "timings"]
RERUN = os.environ.get("TAI_RERUN", "")  # a new e-mail and ID when a case is run again after a fix
NID = "8" if RERUN else "2"
AI = ".frappe-control[data-fieldname=ai_html]"

REPORT: dict = {}
if os.path.exists(OUT):
    REPORT = json.load(open(OUT, encoding="utf-8"))
REPORT.setdefault("tests", {})
REPORT.setdefault("perm", {})
REPORT.setdefault("timings", {})


def save() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    REPORT["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, ensure_ascii=False, indent=1)


def record(tid: str, title: str, user: str, ok: bool, expected: str, actual: str, seconds=None, file=None, shots=(), **extra) -> None:
    REPORT["tests"][tid] = {"title": title, "user": user, "file": file, "expected": expected, "actual": actual, "ok": bool(ok),
                            "seconds": seconds, "shots": list(shots), **extra}
    print(f"{'PASS' if ok else 'FAIL'} {tid} {title} — {actual[:160]}", flush=True)
    save()


def fail(tid: str, title: str, user: str, err: Exception) -> None:
    record(tid, title, user, False, "-", f"error: {type(err).__name__}: {str(err)[:300]}", traceback=traceback.format_exc()[-1500:])


async def snap(page, rel: str, selector: str | None = None, full: bool = False, pad: int = 0) -> str:
    path = os.path.join(IMG, rel)
    await shot(page, path, selector=selector, full=full, pad=pad)
    compact_png(path)
    return os.path.relpath(path, DOCS)


async def visible_page(page) -> str:
    """Mark the desk page container that is on screen (pages scroll inside their own container)."""
    await page.evaluate("""() => { document.querySelectorAll('[data-tai-shot]').forEach(e => e.removeAttribute('data-tai-shot'));
      const c = Array.from(document.querySelectorAll('.page-container')).find(e => e.offsetParent !== null) || document.querySelector('.main-section') || document.body;
      c.setAttribute('data-tai-shot', '1'); }""")
    return '[data-tai-shot="1"]'


def compose(*args):
    return subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], cwd=os.path.join(ROOT, "talent-engine"),
                          capture_output=True, text=True)


def applicant(key: str, **over) -> dict:
    a = dict(next(x for x in DATA["applicants"] if x["key"].endswith(key)))
    a["answers"] = dict(a["answers"])
    a.update(over)
    return a


async def login(page, email: str, password: str, landing: str = "/desk") -> None:
    """Log in through the login API (same session cookie as the login form), then open `landing`."""
    await page.goto(BASE + "/login")
    st = await page.evaluate(
        """([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [email, password])
    assert st == 200, f"login {email}: HTTP {st}"
    if landing:
        await page.goto(BASE + landing)
        await settle(page, 1.5)


FILL_JS = """([v, ans]) => {
  const f = document.getElementById('tai-form');
  for (const [k, x] of Object.entries(v)) { const el = f.querySelector('[name="' + k + '"]'); if (el) { el.value = x; el.dispatchEvent(new Event('change', {bubbles: true})); } }
  for (const [k, x] of Object.entries(ans)) {
    if (Array.isArray(x)) { f.querySelectorAll('[data-qm="' + k + '"]').forEach(c => c.checked = x.includes(c.value)); continue; }
    const el = f.querySelector('[data-q="' + k + '"]'); if (el) el.value = x === null || x === undefined ? '' : String(x); }
  document.getElementById('f-consent').checked = true; }"""


def form_values(a: dict) -> tuple[dict, dict]:
    t = date.today()
    dob = (t.replace(year=t.year - a["age"]) - timedelta(days=120)).isoformat()
    vals = {k: "" if a.get(k) is None else str(a.get(k)) for k in ("applicant_name", "email_id", "phone_number", "nationality", "id_type", "national_id", "height_cm", "weight_kg")}
    vals["date_of_birth"] = dob
    return vals, a["answers"]


async def submit_public(page, opening: str, a: dict, cv: str | None = None, filled_shot: str | None = None, thanks_shot: str | None = None) -> dict:
    t0 = time.time()
    await page.goto(f"{BASE}/ai-apply/new?job_title={opening}")
    await page.wait_for_selector("#tai-form", timeout=60000)
    load_s = round(time.time() - t0, 2)
    vals, ans = form_values(a)
    await page.evaluate(FILL_JS, [vals, ans])
    if cv:
        await page.set_input_files("#f-cv", cv)
    out = {"form_load_s": load_s, "shots": []}
    if filled_shot:
        out["shots"].append(await snap(page, filled_shot, selector="#tai-form"))
    t1 = time.time()
    await page.click("#tai-form button[type=submit]")
    try:
        await page.wait_for_selector(".success", timeout=180000)
        out["ok"] = True
    except Exception:
        out["ok"] = False
        out["errors"] = await page.evaluate("Array.from(document.querySelectorAll('.errors li, .errors')).map(e => e.innerText).join(' | ')")
    out["submit_s"] = round(time.time() - t1, 2)
    out["t_submit"] = t1
    if thanks_shot:
        out["shots"].append(await snap(page, thanks_shot, selector=".formcard"))
    return out


async def wait_final(hr, name: str, timeout: float = 600) -> tuple[str | None, float | None]:
    return await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), timeout, 1.0)


async def assessment(hr, name: str) -> dict:
    return await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": name})


async def open_applicant(hr, name: str, wait_card: bool = True) -> None:
    await hr.goto(f"{BASE}/desk/job-applicant/{name}")
    await settle(hr, 2)
    if wait_card:
        await hr.wait_for_selector(f"{AI} .tai .card", timeout=90000)
        await asyncio.sleep(1.5)


# ============================================================================== files
def prepare_files() -> dict:
    """DOC and RTF from the Word CV (LibreOffice in the engine image) and a bad-quality scan."""
    os.makedirs(TEST_CVS, exist_ok=True)
    out = {"rtf": os.path.join(TEST_CVS, "HR-APP-2026-2018.rtf"), "doc": os.path.join(TEST_CVS, "HR-APP-2026-2018.doc"),
           "bad": os.path.join(TEST_CVS, "HR-APP-2026-2025-bad.jpg")}
    for ext in ("rtf", "doc"):
        if not os.path.exists(out[ext]):
            subprocess.run(["docker", "cp", os.path.join(CVS, "HR-APP-2026-2018.docx"), "talentai-api-1:/tmp/HR-APP-2026-2018.docx"], check=True)
            filt = {"rtf": "rtf", "doc": "doc:MS Word 97"}[ext]
            subprocess.run(["docker", "exec", "talentai-api-1", "sh", "-c",
                            f"cd /tmp && HOME=/tmp soffice -env:UserInstallation=file:///tmp/lo_test --headless --convert-to '{filt}' --outdir /tmp/conv /tmp/HR-APP-2026-2018.docx >/dev/null 2>&1"],
                           check=True, timeout=180)
            subprocess.run(["docker", "cp", f"talentai-api-1:/tmp/conv/HR-APP-2026-2018.{ext}", out[ext]], check=True)
    if not os.path.exists(out["bad"]):
        from PIL import Image, ImageFilter
        import random

        im = Image.open(os.path.join(CVS, "HR-APP-2026-2025.jpg")).convert("L")
        w, h = im.size
        im = im.resize((w // 3, h // 3)).resize((w, h)).filter(ImageFilter.GaussianBlur(1.6)).rotate(2.5, fillcolor=235)
        rnd = random.Random(7)
        px = im.load()
        for _ in range(w * h // 18):
            x, y = rnd.randrange(w), rnd.randrange(h)
            px[x, y] = rnd.choice((40, 90, 200, 255))
        im.save(out["bad"], quality=18)
    return out


# ============================================================================== roles and permissions
USERS = [
    # key, login, password key, role label (Arabic), roles
    ("administrator", "Administrator", "ADMIN_PASSWORD", "Administrator", ["Administrator (كل الصلاحيات)"]),
    ("system_manager", "sysmanager@example.com", "SYSTEM_MANAGER_PASSWORD", "مدير النظام", ["System Manager"]),
    ("hr_manager", "hr.manager@example.com", "HR_MANAGER_PASSWORD", "مدير الموارد البشرية", ["HR Manager", "HR User", "Employee"]),
    ("hr_user", "hr.user@example.com", "HR_USER_PASSWORD", "أخصائي التوظيف", ["HR User", "Employee"]),
    ("interviewer", "interviewer@example.com", "INTERVIEWER_PASSWORD", "المقابِل", ["Interviewer", "Employee"]),
    ("employee", "employee@example.com", "EMPLOYEE_PASSWORD", "موظف", ["Employee"]),
    ("ess", "ess@example.com", "ESS_PASSWORD", "موظف خدمة ذاتية", ["Employee Self Service", "Employee"]),
    ("portal", "portal.applicant@example.com", "PORTAL_PASSWORD", "متقدم بحساب على الموقع", ["Website User"]),
    ("guest", None, None, "زائر / متقدم بلا حساب", ["Guest"]),
]

DENY_JS = r"""() => { const b = document.body.innerText || '';
  return {login: location.pathname.startsWith('/login') || !!document.querySelector('#login_email'),
          denied: /Not Permitted|لا يسمح|غير مسموح|Insufficient Permission|عدم كفاية الإذن|ليس لديك الأذونات|ليس لديك صلاحية|You do not have enough permissions|You need to be logged in|تحتاج إلى تسجيل الدخول|No permission/i.test(b),
          url: location.pathname + location.search, text: b.slice(0, 300)}; }"""


async def screen_state(page, key: str, ctx: dict) -> dict:
    """Open one screen as the page's user and say whether they see it, can edit it, or are denied."""
    u = ctx["url"]
    d: dict = {}
    if key == "cv_file":
        r = await call_status(page, ctx["cv_url"])
        st = "see" if r["status"] == 200 else "deny"
        return {"state": st, "detail": f"HTTP {r['status']}"}
    if key == "cv_analysis":
        if not ctx.get("applicant_open"):
            r = await call_status(page, "/api/method/ido_talent_ai.api.cv_analysis", {"applicant": A(2002)})
            return {"state": "see" if r["status"] == 200 else "deny", "detail": f"API HTTP {r['status']}"}
        await page.evaluate(f"talent_ai.openCvAnalysis({json.dumps(A(2002))})")
        try:
            await page.wait_for_selector(".modal.show .tai .pageview img, .modal.show .msgprint", timeout=90000)
        except Exception:
            pass
        await asyncio.sleep(2)
        ok = await page.evaluate("!!document.querySelector('.modal.show .tai .pageview img')")
        d = {"state": "see" if ok else "deny", "detail": "dialog with the page image and OCR boxes" if ok else "no dialog"}
        d["selector"] = ".modal.show .modal-content"
        return d
    await page.goto(BASE + u)
    await settle(page, 2.5)
    s = await page.evaluate(DENY_JS)
    if s["login"]:
        return {"state": "deny", "detail": "redirected to the login page"}
    if key == "public_form":
        ok = await page.evaluate("!!document.querySelector('#tai-form')")
        return {"state": "edit" if ok else "deny", "detail": "public form (anyone can apply)" if ok else s["text"][:80]}
    if s["denied"]:
        return {"state": "deny", "detail": "Frappe: " + s["text"].strip().split("\n")[0][:90]}
    if key in ("home", "cycle", "ranking", "batch", "pool"):
        sel = {"home": ".tai-home-grid", "cycle": ".tai .mapcard, .tai .map, .tai .mnode", "ranking": ".tai .rankrow, .tai .page-title",
               "batch": ".tai .page-title", "pool": ".tai .page-title"}[key]
        try:
            await page.wait_for_selector(sel, timeout=30000)
        except Exception:
            pass
        info = await page.evaluate(f"""() => ({{has: !!document.querySelector({json.dumps(sel)}),
            off: document.querySelectorAll('.tai-home .off, .tai-home [aria-disabled=true]').length,
            acts: Array.from(document.querySelectorAll('.page-actions button, .page-actions .btn')).filter(b => b.offsetParent).map(b => b.innerText.trim()).filter(Boolean).slice(0, 6)}})""")
        if not info["has"]:
            s2 = await page.evaluate(DENY_JS)
            return {"state": "deny", "detail": (s2["text"].strip().split("\n")[0] or "empty page")[:90]}
        st = "edit" if (key in ("ranking", "batch") and info["acts"]) else "see"
        det = "actions: " + " · ".join(info["acts"]) if info["acts"] else "read only"
        if key == "home" and info["off"]:
            det = f"{info['off']} card(s) shown as «غير متاح لدورك»"
        return {"state": st, "detail": det}
    if key in ("profile", "opening", "applicant", "assessment", "settings"):
        dt = {"profile": "AI Job Profile", "opening": "Job Opening", "applicant": "Job Applicant", "assessment": "Job Applicant", "settings": "AI Recruitment Settings"}[key]
        info = await page.evaluate(f"""() => ({{ok: !!(window.cur_frm && cur_frm.doctype === {json.dumps(dt)} && cur_frm.doc && !cur_frm.doc.__islocal),
            write: !!(window.cur_frm && cur_frm.perm && cur_frm.perm[0] && cur_frm.perm[0].write),
            ai: !!document.querySelector('{AI} .tai .card'),
            score_in_doc: !!(window.cur_frm && cur_frm.doc && cur_frm.doc.ai_score != null),
            decision: Array.from(document.querySelectorAll('.page-actions .inner-group-button, .page-actions button')).some(b => /القرار|Decision/.test(b.innerText)),
            hrms_buttons: Array.from(document.querySelectorAll('.page-actions button')).filter(b => b.offsetParent).map(b => b.innerText.trim()).filter(t => /^(Shortlist|Reject|ترشيح للمقابلة|رفض)$/.test(t))}})""")
        if not info["ok"]:
            return {"state": "deny", "detail": "form did not open"}
        if key == "assessment":
            if info["ai"]:
                ctx["applicant_open"] = True
                return {"state": "edit" if info["decision"] else "see", "detail": ("decision buttons «القرار» + override" if info["decision"] else "read only"),
                        "selector": AI}
            return {"state": "deny", "detail": "the AI section is not shown (permission level 1)" + (" — score not sent to the browser" if not info["score_in_doc"] else "")}
        if key == "applicant":
            ctx["applicant_open"] = info["ai"]
            extra = "; HRMS Shortlist/Reject visible: " + ",".join(info["hrms_buttons"]) if info["hrms_buttons"] else ""
            return {"state": "edit" if info["write"] else "see", "detail": ("can edit the form" if info["write"] else "read only") + extra}
        return {"state": "edit" if info["write"] else "see", "detail": "can edit" if info["write"] else "read only"}
    if key in ("list", "jobs", "audit"):
        dt = {"list": "Job Applicant", "jobs": "AI Recruitment Job", "audit": "AI Recruitment Audit Log"}[key]
        try:
            await page.wait_for_function(f"window.cur_list && cur_list.doctype === {json.dumps(dt)} && cur_list.data", timeout=30000)
        except Exception:
            s2 = await page.evaluate(DENY_JS)
            return {"state": "deny", "detail": (s2["text"].strip().split("\n")[0] or "list did not open")[:90]}
        info = await page.evaluate(f"""() => ({{rows: cur_list.data.length, create: !!(frappe.model.can_create({json.dumps(dt)})),
            ai_cols: Array.from(document.querySelectorAll('.list-row-head .list-row-col')).map(c => c.innerText.trim()).filter(t => /الذكاء|AI/.test(t))}})""")
        det = f"{info['rows']} rows" + (f"; AI columns: {', '.join(info['ai_cols'])}" if info["ai_cols"] else "")
        return {"state": "edit" if (key == "list" and info["create"]) else "see", "detail": det}
    return {"state": "?", "detail": "unknown screen"}


SCREENS = [
    ("home", "الصفحة الرئيسية «التوظيف الذكي»", "/desk/ai-recruitment"),
    ("cycle", "خريطة الدورة", "/desk/talent-ai"),
    ("profile", "ملف المعايير", "/desk/ai-job-profile/{prof}"),
    ("opening", "الشاغر", f"/desk/job-opening/{OP1}"),
    ("list", "قائمة المتقدمين", f"/desk/job-applicant?job_title={OP1}"),
    ("applicant", "طلب المتقدم", f"/desk/job-applicant/{A(2002)}"),
    ("assessment", "قسم تقييم الذكاء", f"/desk/job-applicant/{A(2002)}"),
    ("cv_analysis", "تحليل السيرة", None),
    ("cv_file", "ملف السيرة الأصلي", None),
    ("ranking", "الترتيب", f"/desk/ai-ranking?opening={OP1}"),
    ("batch", "متابعة الدفعة", f"/desk/ai-batch?opening={OP1}"),
    ("pool", "بنك المتقدمين", f"/desk/ai-talent-pool?opening={OP2}"),
    ("jobs", "مهام الذكاء", "/desk/ai-recruitment-job"),
    ("settings", "الإعدادات", "/desk/ai-recruitment-settings"),
    ("audit", "سجل التدقيق", "/desk/ai-recruitment-audit-log"),
    ("public_form", "صفحة التقديم العامة", f"/ai-apply/new?job_title={OP1}"),
]

PROBES = [
    ("get_assessment", "/api/method/ido_talent_ai.api.get_assessment", {"applicant": A(2002)}, "GET"),
    ("ranking", "/api/method/ido_talent_ai.api.ranking", {"job_opening": OP1}, "GET"),
    ("cv_analysis", "/api/method/ido_talent_ai.api.cv_analysis", {"applicant": A(2002)}, "GET"),
    ("talent_pool", "/api/method/ido_talent_ai.api.talent_pool", {"job_opening": OP2}, "GET"),
    ("compare", "/api/method/ido_talent_ai.api.compare", {"applicants": [A(2001), A(2002)]}, "GET"),
    ("export_csv", "/api/method/ido_talent_ai.api.export_ranking_csv", {"job_opening": OP1}, "GET"),
    ("decide", "/api/method/ido_talent_ai.api.decide", {"applicant": A(2002), "status": "Probe", "reason": "probe"}, "POST"),
    ("override", "/api/method/ido_talent_ai.api.override", {"applicant": A(2002), "criterion_key": "edu", "level": 0, "reason": ""}, "POST"),
    ("rescreen", "/api/method/ido_talent_ai.api.rescreen", {"applicant": "probe.missing@example.com"}, "POST"),
    ("rest_applicant", f"/api/resource/Job Applicant/{A(2002)}", None, "GET"),
    ("rest_assessment", "/api/resource/AI Candidate Assessment", {"limit": 1}, "GET"),
    ("rest_audit", "/api/resource/AI Recruitment Audit Log", {"limit": 1}, "GET"),
    ("rest_settings", "/api/resource/AI Recruitment Settings/AI Recruitment Settings", None, "GET"),
    ("cv_file", None, None, "GET"),
]


async def run_roles(b) -> None:
    perm = REPORT["perm"]
    # the facts every user is compared on: the profile name and 2002's private CV file
    adm = await new_page(b, "1366")
    await login(adm, "Administrator", DEV["ADMIN_PASSWORD"])
    prof = (await xcall(adm, "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"}))["ai_profile"]
    cv_url = (await xcall(adm, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": A(2002), "fieldname": "resume_attachment"}))["resume_attachment"]
    roles = await xcall(adm, "frappe.client.get_list", {"doctype": "Role", "fields": ["name", "desk_access", "disabled"], "limit_page_length": 500, "order_by": "name asc"})
    await adm.context.close()
    perm["roles_on_site"] = [r["name"] + ("" if r["desk_access"] else " (no desk)") for r in roles]
    perm["recruitment_roles"] = ["Administrator", "System Manager", "HR Manager", "HR User", "Interviewer", "Employee", "Employee Self Service", "Guest", "Website User (no role)"]
    perm["not_found"] = "No «Hiring Manager» or department-manager role exists in Frappe HR v16 (checked the full role list); a hiring manager is an Employee who may also be an Interviewer."
    perm["screens"] = [{"key": k, "label": lbl} for k, lbl, _ in SCREENS] + [{"key": "console", "label": "Talent Console"}]
    perm["users"] = [{"key": k, "login": e or "Guest", "label": lbl, "roles": r} for k, e, _, lbl, r in USERS]
    perm.setdefault("matrix", {})
    perm.setdefault("probes", {})
    save()
    for key, email, pwkey, label, _roles in USERS:
        page = await new_page(b, "1366")
        try:
            if email:
                await login(page, email, DEV[pwkey], landing="/desk" if key != "portal" else "/")
            else:
                await page.goto(BASE + "/jobs")
                await settle(page, 1)
            ctx = {"cv_url": cv_url}
            row = {}
            seen_hash: dict[str, str] = {}
            for skey, slabel, url in SCREENS:
                ctx["url"] = (url or "").format(prof=prof)
                try:
                    st = await screen_state(page, skey, ctx)
                except Exception as e:  # keep going: one screen failing must not hide the others
                    st = {"state": "?", "detail": f"error: {e}"[:120]}
                if skey != "cv_file":
                    sel = st.pop("selector", None)
                    path = await snap(page, f"roles/{key}_{skey}.png", selector=sel or await visible_page(page) if skey not in ("public_form",) and not st["detail"].startswith("redirected") else None)
                    h = hashlib.sha1(open(os.path.join(DOCS, path), "rb").read()).hexdigest()
                    if h in seen_hash:  # same picture as an earlier screen of this user (login page): keep one file
                        os.remove(os.path.join(DOCS, path))
                        path = seen_hash[h]
                    seen_hash[h] = path
                    st["shot"] = path
                if skey == "cv_analysis":
                    await page.evaluate("window.cur_dialog && cur_dialog.hide && cur_dialog.hide()")
                row[skey] = st
                print(f"  {key:15} {skey:12} {st['state']:5} {st['detail'][:90]}", flush=True)
            row["console"] = {"state": "deny", "detail": "separate login; only the console user (Nadine) has an account"}
            perm["matrix"][key] = row
            # API probes from a page of the site (same cookies)
            if not page.url.startswith(BASE) or "/desk" not in page.url and key not in ("portal", "guest"):
                await page.goto(BASE + "/desk")
            pr = {}
            for pkey, path, args, method in PROBES:
                needles = {"rest_applicant": ['"ai_score"', '"national_id"'], "rest_settings": [ENG["TENANT_API_KEY"]]}.get(pkey)
                r = await call_status(page, path or cv_url, args, method, needles)
                extra = ""
                if pkey == "rest_applicant" and r["status"] == 200:
                    extra = ("AI fields in the reply" if r["found"].get("0") else "no AI fields") + ("; national ID in the reply" if r["found"].get("1") else "")
                if pkey == "rest_settings" and r["status"] == 200:
                    extra = "secrets masked" if not r["found"].get("0") else "API KEY IN CLEAR"
                pr[pkey] = {"status": r["status"], "note": extra}
            perm["probes"][key] = pr
            save()
            print(f"  {key:15} probes " + " ".join(f"{k}={v['status']}" for k, v in pr.items()), flush=True)
        finally:
            await page.context.close()
    # the console: only Nadine logs in
    page = await new_page(b, "1366")
    await page.goto(CONSOLE + "/console/login")
    await settle(page, 1)
    perm["console_login_shot"] = await snap(page, "roles/console_login.png", full=False)
    await page.context.close()
    save()
    evaluate_roles()


def evaluate_roles() -> None:
    """Turn the matrix and the probes into checks."""
    perm = REPORT["perm"]
    m, p = perm["matrix"], perm["probes"]
    hr = ("administrator", "system_manager", "hr_manager", "hr_user")
    non_hr = ("interviewer", "employee", "ess", "portal", "guest")
    secret_screens = ("assessment", "cv_analysis", "cv_file", "ranking", "batch", "pool", "jobs", "settings", "audit", "list", "applicant", "home", "cycle", "profile")
    leaks = [f"{u}:{s}" for u in non_hr for s in secret_screens if m.get(u, {}).get(s, {}).get("state") in ("see", "edit")]
    api_leaks = [f"{u}:{k}={v['status']}" for u in non_hr for k, v in p.get(u, {}).items() if v["status"] == 200]
    record("R01", "Employee, Interviewer, self-service, website user and guest never see a score, an assessment or a CV", ", ".join(non_hr),
           not leaks and not api_leaks, "every AI screen and API call refused (403 or login page)",
           f"screens open: {leaks or 'none'}; API 200: {api_leaks or 'none'}")
    hr_ok = all(m.get(u, {}).get("assessment", {}).get("state") == "edit" for u in hr)
    record("R02", "HR Manager, HR User, System Manager and Administrator see the assessment with the decision buttons", ", ".join(hr), hr_ok,
           "assessment section + «القرار» buttons", "; ".join(f"{u}: {m.get(u, {}).get('assessment', {}).get('state')}" for u in hr))
    dec = {u: (p.get(u, {}).get("decide", {}).get("status"), p.get(u, {}).get("override", {}).get("status")) for u in hr + non_hr}
    ok = all(dec[u] == (417, 417) for u in hr) and all(dec[u][0] in (401, 403) and dec[u][1] in (401, 403) for u in non_hr)
    record("R03", "Shortlist / reject / override are HR-only (server side)", "all", ok,
           "HR: the call passes the permission check and stops at validation (417); others: 403",
           "; ".join(f"{u}: decide {a}, override {b}" for u, (a, b) in dec.items()))
    s_hr_user = m.get("hr_user", {}).get("settings", {}).get("state")
    record("R04", "Settings: HR Manager and System Manager edit, HR User is refused", "hr_manager, hr_user", s_hr_user == "deny" and m.get("hr_manager", {}).get("settings", {}).get("state") == "edit",
           "HR Manager edit; HR User denied", f"HR Manager {m.get('hr_manager', {}).get('settings', {}).get('state')}; HR User {s_hr_user}")
    hrms_btn = [u for u in hr if "HRMS Shortlist/Reject visible" in m.get(u, {}).get("applicant", {}).get("detail", "")]
    record("R05", "HRMS's own Shortlist/Reject buttons (no reason) are replaced by «القرار»", ", ".join(hr), not hrms_btn,
           "no Shortlist/Reject outside «القرار»", f"visible for: {hrms_btn or 'nobody'}")
    rest = {u: p.get(u, {}).get("rest_applicant", {}) for u in hr}
    record("R06", "The REST API gives HR the AI fields and refuses everyone else", "all",
           all(v.get("status") == 200 for v in rest.values()) and all(p.get(u, {}).get("rest_applicant", {}).get("status") in (401, 403) for u in non_hr),
           "HR 200, others 403", "; ".join(f"{u}: {p.get(u, {}).get('rest_applicant', {}).get('status')}" for u in hr + non_hr))
    sett = p.get("hr_manager", {}).get("rest_settings", {})
    record("R07", "Settings read through the API never show the secrets", "hr_manager", sett.get("status") == 200 and sett.get("note") == "secrets masked",
           "API key and secrets masked", f"HTTP {sett.get('status')}, {sett.get('note')}")


async def run_landing(b) -> None:
    """HR users land on «التوظيف الذكي» after the real login form, in Arabic."""
    from pw import login_desk

    for key, email, pwkey in (("hr_manager", "hr.manager@example.com", "HR_MANAGER_PASSWORD"), ("hr_user", "hr.user@example.com", "HR_USER_PASSWORD")):
        page = await new_page(b, "1366", scale=1.5)
        try:
            await page.goto(BASE + "/login")
            await settle(page, 1)
            shots = [await snap(page, f"test/R08_{key}_login.png", selector=".page-card, .login-content, form", pad=12)] if key == "hr_manager" else []
            secs = await login_desk(page, email, DEV[pwkey], via_form=True)
            await page.wait_for_selector(".tai-home-grid", timeout=60000)
            await settle(page, 1.5)
            url = page.url.replace(BASE, "")
            lang = await page.evaluate("frappe.boot.lang")
            shots.append(await snap(page, f"test/R08_{key}_home.png", selector=await visible_page(page)))
            record(f"R08_{key}", f"{key} lands on «التوظيف الذكي» in Arabic after the login form", email, url.startswith("/desk/ai-recruitment") and lang == "ar",
                   "/desk/ai-recruitment, language ar", f"{url}, language {lang}, {secs}s", seconds=secs, shots=shots)
        except Exception as e:
            fail(f"R08_{key}", "landing page", email, e)
        finally:
            await page.context.close()


async def run_other_application(b) -> None:
    """An applicant never sees another application (no portal account, or a website account)."""
    page = await new_page(b, "1366")
    try:
        await login(page, "portal.applicant@example.com", DEV["PORTAL_PASSWORD"], landing="/")
        probes = {}
        for k, path in (("rest", f"/api/resource/Job Applicant/{A(2001)}"), ("list", "/api/resource/Job Applicant"),
                        ("assessment", "/api/method/ido_talent_ai.api.get_assessment?applicant=" + A(2001))):
            probes[k] = (await call_status(page, path))["status"]
        await page.goto(f"{BASE}/desk/job-applicant/{A(2001)}")
        await settle(page, 2)
        s = await page.evaluate(DENY_JS)
        shot1 = await snap(page, "test/R09_portal_other_application.png", full=False)
        g = await new_page(b, "1366")
        gp = {}
        for k, path in (("rest", f"/api/resource/Job Applicant/{A(2001)}"), ("assessment", "/api/method/ido_talent_ai.api.get_assessment?applicant=" + A(2001))):
            await g.goto(BASE + "/jobs")
            gp[k] = (await call_status(g, path))["status"]
        await g.goto(f"{BASE}/desk/job-applicant/{A(2001)}")
        await settle(g, 2)
        shot2 = await snap(g, "test/R09_guest_other_application.png", full=False)
        await g.context.close()
        ok = all(v in (401, 403) for v in list(probes.values()) + list(gp.values()))
        record("R09", "An applicant cannot open another applicant's application", "portal.applicant@example.com, Guest", ok,
               "403 on every call; the desk page refuses", f"website user {probes}, desk: {s['url']} {'denied' if s['denied'] or s['login'] else 'OPEN'}; guest {gp}",
               shots=[shot1, shot2])
    except Exception as e:
        fail("R09", "applicant isolation", "portal", e)
    finally:
        await page.context.close()


# ============================================================================== CV types
CV_CASES = [
    # id, title, demo key, file (relative to CVS or a prepared file key), new e-mail, new national id
    ("C01", "Arabic scanned image (JPG, OCR)", "2002", "HR-APP-2026-2002.jpg", "t.cv.scan"),
    ("C02", "Arabic text PDF", "2001", "HR-APP-2026-2001.pdf", "t.cv.arpdf"),
    ("C03", "English PDF", "2022", "HR-APP-2026-2022.pdf", "t.cv.enpdf"),
    ("C04", "Word (DOCX)", "2018", "HR-APP-2026-2018.docx", "t.cv.docx"),
    ("C05", "RTF (converted from the Word CV)", "2018", "rtf", "t.cv.rtf"),
    ("C06", "DOC, Word 97 (converted from the Word CV)", "2018", "doc", "t.cv.doc"),
    ("C07", "No CV", "2003", None, "t.cv.none"),
    ("C08", "Corrupt PDF", "2013", "HR-APP-2026-2013.pdf", "t.cv.corrupt"),
    ("C09", "Bad-quality image (blurred, noisy, JPEG quality 18)", "2025", "bad", "t.cv.badimg"),
]


async def run_cvtypes(b, files: dict) -> None:
    hr = await new_page(b, "1366", scale=1.5)
    await login(hr, "hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])
    guest = await new_page(b, "1366", scale=1.5)
    try:
        only = set(filter(None, os.environ.get("TAI_ONLY", "").split(",")))
        rerun = os.environ.get("TAI_RERUN", "")  # a new e-mail and ID when a case is run again after a fix
        for i, (tid, title, key, f, mail) in enumerate(CV_CASES):
            if only and tid not in only:
                continue
            try:
                path = None if f is None else (files[f] if f in files else os.path.join(CVS, f))
                email = f"{mail}{rerun}@example.com"
                a = applicant(key, email_id=email, national_id=f"1000099{'2' if rerun else '1'}{i:02d}")
                sub = await submit_public(guest, OP1, a, path, filled_shot=f"test/{tid}_form.png" if tid in ("C01", "C07") else None,
                                          thanks_shot=f"test/{tid}_thanks.png" if tid == "C01" else None)
                if not sub.get("ok"):
                    record(tid, title, "Guest → HR Manager", False, "saved", f"form refused: {sub.get('errors')}", file=os.path.basename(path or "") or None)
                    continue
                t_saved = time.time() - sub["t_submit"]
                status, waited = await wait_final(hr, email, 600)
                total = round(time.time() - sub["t_submit"], 1)
                d = await assessment(hr, email)
                res = d.get("result") or {}
                cv = res.get("cv") or {}
                vers = res.get("versions") or {}
                flags = res.get("flags") or []
                await open_applicant(hr, email)
                shots = sub["shots"] + [await snap(hr, f"test/{tid}_assessment.png", selector=AI)]
                if path and cv.get("status") == "ready":
                    await hr.evaluate(f"talent_ai.openCvAnalysis({json.dumps(email)})")
                    try:
                        await hr.wait_for_selector(".modal.show .tai .pageview img", timeout=90000)
                        await asyncio.sleep(2)
                        shots.append(await snap(hr, f"test/{tid}_cv_analysis.png", selector=".modal.show .modal-content"))
                    except Exception:
                        pass
                    await hr.evaluate("window.cur_dialog && cur_dialog.hide()")
                note = d.get("cv_note") or ""
                exp = {"C07": "Completed from the answers; no CV",
                       "C08": "the platform refuses the file, the application is saved and assessed from the answers (decision 14)",
                       "C09": "read with OCR; low confidence flagged if under the threshold"}.get(tid, "CV read, redacted, quotes verified")
                if tid == "C08":
                    ok = status in ("Completed", "Needs Review") and not cv and bool(note)
                elif tid == "C07":
                    ok = status in ("Completed", "Needs Review") and not cv
                elif tid == "C09":
                    ok = status in ("Completed", "Needs Review") and (cv.get("status") == "ready" or "cv_unreadable" in flags)
                else:
                    ok = status in ("Completed", "Needs Review") and cv.get("status") == "ready"
                actual = (f"{status}; score {res.get('score')} ({res.get('band')}); method {cv.get('method') or '-'}"
                          + (f", OCR confidence {cv.get('ocr_confidence'):.2f}" if cv.get("ocr_confidence") is not None else "")
                          + (f"; flags {', '.join(flags)}" if flags else "") + (f"; note: {note}" if note else ""))
                record(tid, title, "Guest → HR Manager", ok, exp, actual, seconds=total, file=os.path.basename(path) if path else None, shots=shots,
                       timing={"form_load_s": sub["form_load_s"], "submit_s": sub["submit_s"], "until_result_s": total,
                               "pipeline_s": round((vers.get("total_ms") or 0) / 1000, 1), "stages": {s.get("key"): s.get("ms") for s in res.get("stages") or []}},
                       applicant=email)
            except Exception as e:
                fail(tid, title, "Guest → HR Manager", e)
    finally:
        await hr.context.close()
        await guest.context.close()


# ============================================================================== special cases
async def crit(d: dict, key: str) -> dict:
    return next((c for c in (d.get("result") or {}).get("criteria", []) if c.get("key") == key), {})


async def run_cases(b) -> None:
    hr = await new_page(b, "1366", scale=1.5)
    await login(hr, "hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])
    guest = await new_page(b, "1366", scale=1.5)
    only = set(filter(None, os.environ.get("TAI_ONLY", "").split(",")))
    cases = [("K01", lambda: case_strength(hr)), ("K02", lambda: case_not_eligible(hr, guest)), ("K03a", lambda: case_blank_height_public(guest)),
             ("K04", lambda: case_blank_vs_zero(hr)), ("K05", lambda: case_contradiction(hr)), ("K06", lambda: case_duplicate(hr)),
             ("K07", lambda: case_edit_after(hr)), ("K08", lambda: case_override(hr)), ("K09", lambda: case_decisions(hr)), ("K10", lambda: case_csv(hr)),
             ("K11", lambda: case_compare(hr)), ("K12", lambda: case_pool(hr)), ("K13", lambda: case_xss(hr, guest)), ("K14", lambda: case_weights(hr)),
             ("K15", lambda: case_engine_down(hr, guest))]
    try:
        for tid, fn in cases:
            if not only or tid in only:
                await fn()
    finally:
        await hr.context.close()
        await guest.context.close()


async def case_strength(hr) -> None:
    try:
        rows = []
        shots = []
        for n, label in ((2001, "strong"), (2004, "medium"), (2005, "weak")):
            d = await assessment(hr, A(n))
            r = d["result"]
            rows.append((n, label, r.get("score"), r.get("band"), r.get("rank")))
            await open_applicant(hr, A(n))
            shots.append(await snap(hr, f"test/K01_{label}_{n}.png", selector=f"{AI} .tai > .card:first-child"))
        ok = rows[0][3] == "high" and rows[1][3] == "medium" and rows[2][3] == "low"
        record("K01", "Strong, medium and weak applicants", "HR Manager", ok, "bands high / medium / low",
               "; ".join(f"{n} ({lbl}): {s} {bd}, rank {rk}" for n, lbl, s, bd, rk in rows), shots=shots)
    except Exception as e:
        fail("K01", "strong/medium/weak", "HR Manager", e)


async def case_not_eligible(hr, guest) -> None:
    try:
        a = applicant("2011", email_id=f"t.noteligible{RERUN}@example.com", national_id=f"100009{NID}201", height_cm=172)
        sub = await submit_public(guest, OP1, a, None)
        status, _ = await wait_final(hr, a["email_id"], 300)
        d = await assessment(hr, a["email_id"])
        r = d["result"]
        failed = [c for c in r.get("eligibility_checks", []) if c.get("ok") is False]
        await open_applicant(hr, a["email_id"])
        shots = [await snap(hr, "test/K02_not_eligible.png", selector=f"{AI} .tai > .card:first-child")]
        rk = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        in_ranked = any(x.get("applicant") == a["email_id"] for x in rk["ranked"])
        ok = r.get("eligibility") == "not_eligible" and len(failed) == 2 and not in_ranked
        record("K02", "Not eligible: height 172 cm and nationality Egypt", "Guest → HR Manager", ok,
               "not eligible with both reasons, kept out of the ranking, score shown in grey",
               f"{status}; eligibility {r.get('eligibility')}; failed rules: " + " | ".join(c.get("text_ar", "") for c in failed) + f"; ranked: {in_ranked}",
               seconds=round(time.time() - sub["t_submit"], 1), shots=shots, applicant=a["email_id"])
    except Exception as e:
        fail("K02", "not eligible", "HR Manager", e)


async def case_blank_height_public(guest) -> None:
    try:
        a = applicant("2004", email_id=f"t.blankheight{RERUN}@example.com", national_id=f"100009{NID}202", height_cm=None)
        await guest.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await guest.wait_for_selector("#tai-form", timeout=60000)
        vals, ans = form_values(a)
        await guest.evaluate(FILL_JS, [vals, ans])
        await guest.click("#tai-form button[type=submit]")
        await asyncio.sleep(1.5)
        errs = await guest.evaluate("document.querySelector('#tai-form') ? document.querySelector('#tai-form').innerText : ''")
        shot1 = await snap(guest, "test/K03_public_form_height_required.png", selector=".errors, #tai-form .note.danger, #tai-form", pad=6)
        ok = "الطول مطلوب" in errs
        record("K03a", "Public form: height left blank on an opening with a height rule", "Guest", ok,
               "the form asks for the height before sending (the console case K03b shows the engine side)",
               "message «الطول مطلوب لهذا الشاغر» shown" if ok else "no message", shots=[shot1])
    except Exception as e:
        fail("K03a", "blank height (public form)", "Guest", e)


async def case_blank_vs_zero(hr) -> None:
    try:
        blank = await assessment(hr, A(2021))
        zero = await assessment(hr, A(2006))
        cb, cz = await crit(blank, "supervision"), await crit(zero, "supervision")
        ans_b = next((x.get("answer") for x in (await xcall(hr, "frappe.client.get", {"doctype": "Job Applicant", "name": A(2021)}))["ai_answers"] if x["question_key"] == "years_sup"), None)
        ans_z = next((x.get("answer") for x in (await xcall(hr, "frappe.client.get", {"doctype": "Job Applicant", "name": A(2006)}))["ai_answers"] if x["question_key"] == "years_sup"), None)
        shots = []
        for n in (2021, 2006):
            await open_applicant(hr, A(n))
            await hr.evaluate("""() => { const t = Array.from(document.querySelectorAll('.frappe-control[data-fieldname=ai_html] .tai .card')).find(c => /المعايير والأدلة|Criteria and evidence/.test(c.innerText)); if (t) t.setAttribute('data-tai-crit', '1'); }""")
            shots.append(await snap(hr, f"test/K04_{'blank' if n == 2021 else 'zero'}_{n}.png", selector=f"{AI} [data-tai-crit='1']"))
        ok = cb.get("missing_evidence") and not cz.get("missing_evidence") and cz.get("level") == 0 and "missing_evidence" in (blank["result"].get("flags") or [])
        record("K04", "Blank answer vs the answer 0", "HR Manager", ok,
               "blank → level 0 + «دليل ناقص» flag (needs review on a mandatory criterion); 0 → level 0 with the evidence «0», no flag",
               f"2021 (no CV) years_sup={ans_b!r}: level {cb.get('level')}, missing_evidence {cb.get('missing_evidence')}, eligibility {blank['result'].get('eligibility')}; "
               f"2006 years_sup={ans_z!r}: level {cz.get('level')}, evidence {cz.get('evidence')!r}, missing_evidence {cz.get('missing_evidence')}", shots=shots)
    except Exception as e:
        fail("K04", "blank vs zero", "HR Manager", e)


async def case_contradiction(hr) -> None:
    try:
        d = await assessment(hr, A(2012))
        r = d["result"]
        c = next((x for x in r["criteria"] if x.get("contradiction")), {})
        await open_applicant(hr, A(2012))
        shots = [await snap(hr, "test/K05_contradiction_head.png", selector=f"{AI} .tai > .card:first-child")]
        await hr.evaluate("""() => { const t = Array.from(document.querySelectorAll('.frappe-control[data-fieldname=ai_html] .tai .card')).find(c => /المعايير والأدلة|Criteria and evidence/.test(c.innerText)); if (t) t.setAttribute('data-tai-crit', '1'); }""")
        shots.append(await snap(hr, "test/K05_contradiction_criteria.png", selector=f"{AI} [data-tai-crit='1']"))
        ok = "contradiction" in (r.get("flags") or []) and c and c.get("level") == min(x for x in (c.get("form_level"), c.get("cv_level")) if x is not None)
        record("K05", "The answer says one thing, the CV another", "HR Manager", bool(ok),
               "contradiction flag, the lower level is used, needs review before any decision",
               f"flags {r.get('flags')}; {c.get('key')}: form level {c.get('form_level')}, CV level {c.get('cv_level')} → used {c.get('level')}; quote «{(c.get('cv_quote') or c.get('evidence') or '')[:60]}»",
               shots=shots)
    except Exception as e:
        fail("K05", "contradiction", "HR Manager", e)


async def case_duplicate(hr) -> None:
    try:
        out = []
        mail = {n: applicant(str(n))["email_id"] for n in (2015, 2016, 2024, 2003)}
        for dup, orig in ((2016, 2015), (2024, 2003)):
            v = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": mail[dup], "fieldname": ["ai_duplicate_of", "applicant_name"]})
            out.append((dup, mail[orig], v.get("ai_duplicate_of")))
        rk = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        dup_group = {x.get("applicant") for x in rk["groups"]["duplicate"]}
        await open_applicant(hr, mail[2016])
        shots = [await snap(hr, "test/K06_duplicate.png", selector=f"{AI} .tai")]
        ok = all(o == orig for _, orig, o in out) and {mail[2016], mail[2024]} <= dup_group
        record("K06", "Duplicate applications (same national ID, another e-mail)", "HR Manager", ok,
               "linked to the original, grey, only the original is ranked, nothing deleted",
               "; ".join(f"{d} → {o}" for d, _, o in out) + f"; in the duplicate group: {sorted(dup_group)}", shots=shots)
    except Exception as e:
        fail("K06", "duplicate", "HR Manager", e)


async def case_edit_after(hr) -> None:
    try:
        name = A(2004)
        before = (await assessment(hr, name))["result"].get("score")
        await hr.goto(f"{BASE}/desk/job-applicant/{name}")
        await settle(hr, 3)
        await hr.evaluate("""(async () => { const r = cur_frm.doc.ai_answers.find(x => x.question_key === 'years_sup'); r.answer = '6'; cur_frm.dirty(); await cur_frm.save(); })()""")
        stale, t_stale = await wait_value(hr, "Job Applicant", name, "ai_stale", lambda v: v == 1, 60)
        await open_applicant(hr, name)
        shots = [await snap(hr, "test/K07_stale_banner.png", selector=f"{AI} .tai > .note.grey, {AI} .tai > .card:first-child")]
        rk = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        in_stale = any(x.get("applicant") == name for x in rk["groups"]["stale"])
        t0 = time.time()
        await xcall(hr, "ido_talent_ai.api.rescreen", {"applicant": name})
        back, _ = await wait_value(hr, "Job Applicant", name, "ai_stale", lambda v: v == 0, 300)
        st, _ = await wait_final(hr, name, 300)
        after = (await assessment(hr, name))["result"].get("score")
        secs = round(time.time() - t0, 1)
        await open_applicant(hr, name)
        shots.append(await snap(hr, "test/K07_rescored.png", selector=f"{AI} .tai > .card:first-child"))
        rk2 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        ranked = any(x.get("applicant") == name for x in rk2["ranked"])
        ok = stale == 1 and in_stale and back == 0 and ranked and after != before
        record("K07", "Editing an answer after the evaluation", "HR Manager", ok,
               "result marked stale (grey), out of the ranking; re-score → new score, ranked again",
               f"stale {stale} after {t_stale}s; in stale group {in_stale}; score {before} → {after} after re-score ({secs}s, {st}); ranked again {ranked}",
               seconds=secs, shots=shots, score_before=before, score_after=after)
    except Exception as e:
        fail("K07", "edit after evaluation", "HR Manager", e)


async def case_override(hr) -> None:
    try:
        name = A(2002)
        d = await assessment(hr, name)
        before = d["result"]["score"]
        target = next(c for c in d["result"]["criteria"] if c.get("effective_level", c.get("level")) < 100 and c.get("overridden_level") is None)
        no_reason = await xcall(hr, "ido_talent_ai.api.override", {"applicant": name, "criterion_key": target["key"], "level": 100, "reason": "  "})
        # the dialog in the browser: empty reason first, then a real one
        await open_applicant(hr, name)
        await hr.evaluate(f"window.__d = talent_ai_form.override(cur_frm, {json.dumps(target['key'])}, {json.dumps(target.get('text') or target['key'])}, {int(target.get('effective_level', target.get('level') or 0))})")
        await hr.wait_for_selector(".modal.show [data-fieldname=reason] textarea", timeout=20000)
        await asyncio.sleep(0.8)
        await hr.evaluate("window.__d.set_value('level', '100')")
        await hr.evaluate("window.__d.get_primary_btn().click()")  # empty reason: refused in the browser too
        await asyncio.sleep(1.2)
        shots = [await snap(hr, "test/K08_override_no_reason.png")]
        await hr.evaluate("frappe.hide_msgprint()")
        await asyncio.sleep(0.8)
        await hr.evaluate("window.__d.set_value('reason', 'شهادة الدورة اتشافت أصلية في المقابلة الأولية')")
        await asyncio.sleep(0.5)
        shots.append(await snap(hr, "test/K08_override_dialog.png", selector=".modal.show .modal-content"))
        await hr.evaluate("window.__d.get_primary_btn().click()")
        await asyncio.sleep(3)
        after = (await assessment(hr, name))["result"]
        c2 = next(c for c in after["criteria"] if c["key"] == target["key"])
        await open_applicant(hr, name)
        await hr.evaluate("""() => { const t = Array.from(document.querySelectorAll('.frappe-control[data-fieldname=ai_html] .tai .card')).find(c => /المعايير والأدلة|Criteria and evidence/.test(c.innerText)); if (t) t.setAttribute('data-tai-crit', '1'); }""")
        shots.append(await snap(hr, "test/K08_override_done.png", selector=f"{AI} [data-tai-crit='1']"))
        audit = await xcall(hr, "frappe.client.get_list", {"doctype": "AI Recruitment Audit Log", "filters": {"action": "hr.override", "reference_name": name}, "fields": ["actor", "reason"], "limit_page_length": 5})
        ok = isinstance(no_reason, dict) and "__error__" in no_reason and c2.get("overridden_level") == 100 and after["score"] != before and audit
        record("K08", "Override one criterion, without and with a reason", "HR Manager", bool(ok),
               "no reason → refused; with a reason → new level, new score, «تعديل HR» tag, audit row",
               f"no reason: {no_reason.get('__error__', 'ACCEPTED')[:60] if isinstance(no_reason, dict) else no_reason}; {target['key']} → {c2.get('overridden_level')}; score {before} → {after['score']}; audit {len(audit)} row(s)",
               shots=shots, criterion=target["key"], criterion_text=target.get("text"), level_before=target.get("effective_level", target.get("level")),
               score_before=before, score_after=after["score"])
    except Exception as e:
        fail("K08", "override", "HR Manager", e)


async def case_decisions(hr) -> None:
    try:
        shots = []
        res = {}
        bad = await xcall(hr, "ido_talent_ai.api.decide", {"applicant": A(2001), "status": "Rejected", "reason": " "})
        for n, status, label, reason in ((2001, "Shortlisted", "ترشيح للمقابلة", "خبرة إشراف 7 سنوات ورخصة سارية — مناسب للمقابلة"),
                                         (2003, "Hold", "تعليق", "ننتظر شهادة الإسعافات الأولية المحدّثة"),
                                         (2020, "Rejected", "رفض", "الوزن المصرّح به أعلى من شرط الشاغر")):
            await hr.goto(f"{BASE}/desk/job-applicant/{A(n)}")
            await settle(hr, 3)
            await hr.evaluate("window.__d = null")
            await hr.evaluate(f"(() => {{ const before = cur_dialog; talent_ai_form.decide(cur_frm, {json.dumps(status)}); window.__d = cur_dialog; }})()")
            await hr.wait_for_selector(".modal.show [data-fieldname=reason] textarea", timeout=20000)
            await asyncio.sleep(0.6)
            if n == 2001:  # empty reason first
                await hr.evaluate("window.__d.get_primary_btn().click()")
                await asyncio.sleep(1.2)
                shots.append(await snap(hr, "test/K09_decision_no_reason.png"))
                await hr.evaluate("frappe.hide_msgprint()")
                await asyncio.sleep(0.8)
            await hr.evaluate(f"window.__d.set_value('reason', {json.dumps(reason)})")
            await asyncio.sleep(0.4)
            if n == 2001:
                shots.append(await snap(hr, "test/K09_decision_dialog.png", selector=".modal.show .modal-content"))
            await hr.evaluate("window.__d.get_primary_btn().click()")
            await asyncio.sleep(3)
            v = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": A(n), "fieldname": ["status", "ai_decided_by", "ai_decision_reason"]})
            res[n] = v
        await open_applicant(hr, A(2001))
        await hr.evaluate("""() => { const t = Array.from(document.querySelectorAll('.frappe-control[data-fieldname=ai_html] .tai .card')).find(c => /قرار الموارد البشرية|HR decision/.test(c.innerText)); if (t) t.setAttribute('data-tai-dec', '1'); }""")
        shots.append(await snap(hr, "test/K09_decision_done.png", selector=f"{AI} [data-tai-dec='1']"))
        audits = await xcall(hr, "frappe.client.get_list", {"doctype": "AI Recruitment Audit Log", "filters": {"action": "hr.decision"}, "fields": ["reference_name", "actor", "reason"], "limit_page_length": 50})
        ok = isinstance(bad, dict) and "__error__" in bad and res[2001]["status"] == "Shortlisted" and res[2003]["status"] == "Hold" and res[2020]["status"] == "Rejected" and len(audits) >= 3
        record("K09", "Shortlist, hold and reject, each with a reason; no reason → refused", "HR Manager", ok,
               "status changes only through HR, with the reason, the person and the time in the audit log",
               "; ".join(f"{n}: {v['status']} by {v['ai_decided_by']}" for n, v in res.items()) + f"; empty reason: {'refused' if isinstance(bad, dict) and bad.get('__error__') else 'ACCEPTED'}; audit rows {len(audits)}",
               shots=shots)
    except Exception as e:
        fail("K09", "decisions", "HR Manager", e)


async def case_csv(hr) -> None:
    try:
        await hr.goto(f"{BASE}/desk/ai-ranking?opening={OP1}")
        await settle(hr, 3)
        path = os.path.join(SCRATCH, "ranking.csv")
        os.makedirs(SCRATCH, exist_ok=True)
        fname = "ranking.csv"
        try:  # the button opens the CSV in a new tab, which downloads it
            async with hr.context.expect_page(timeout=30000) as pi:
                await hr.evaluate("""() => { const b = Array.from(document.querySelectorAll('.page-actions button, .page-actions .btn')).find(x => /CSV|تصدير/.test(x.innerText)); b.click(); }""")
            popup = await pi.value
            d = await popup.wait_for_event("download", timeout=60000)
            await d.save_as(path)
            fname = d.suggested_filename
            via = "button (download)"
        except Exception:
            b64 = await hr.evaluate(f"fetch('/api/method/ido_talent_ai.api.export_ranking_csv?job_opening={OP1}').then(r => r.arrayBuffer()).then(b => btoa(String.fromCharCode(...new Uint8Array(b))))")
            import base64
            open(path, "wb").write(base64.b64decode(b64))
            via = "same URL fetched by the page"
        raw = open(path, "rb").read()
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        head = rows[0] if rows else []
        ids = [r for r in rows[1:] if any(c.startswith("10000") and len(c) == 10 for c in r)]
        ok = raw.startswith(b"\xef\xbb\xbf") and "الترتيب" in ",".join(head) and len(rows) > 10 and not ids
        record("K10", "Export the ranking to CSV (Excel)", "HR Manager", ok, "UTF-8 with BOM, Arabic header, one row per applicant, no national ID",
               f"{len(rows) - 1} rows via {via}; header: {' | '.join(head[:8])}; national IDs in the file: {len(ids)}", file=fname)
    except Exception as e:
        fail("K10", "CSV", "HR Manager", e)


async def case_compare(hr) -> None:
    try:
        await hr.goto(f"{BASE}/desk/ai-ranking?opening={OP1}")
        await settle(hr, 3)
        await hr.wait_for_selector(".tai .rankrow [data-sel]", timeout=60000)
        boxes = hr.locator(".tai .rankrow [data-sel]")
        for i in range(3):
            await boxes.nth(i).check()
        shots = [await snap(hr, "test/K11_ranking_selected.png", selector=await visible_page(hr))]
        await hr.evaluate("""() => { const b = Array.from(document.querySelectorAll('.page-actions button, .page-actions .btn')).find(x => /مقارنة|Compare/.test(x.innerText)); b.click(); }""")
        await hr.wait_for_selector(".modal.show .tai table.cmptable", timeout=60000)
        await asyncio.sleep(2)
        shots.append(await snap(hr, "test/K11_compare.png", selector=".modal.show .modal-content"))
        n = await hr.evaluate("document.querySelectorAll('.modal.show table.cmptable thead th').length")
        await hr.evaluate("cur_dialog && cur_dialog.hide()")
        record("K11", "Compare three ranked applicants side by side", "HR Manager", n >= 4, "3 columns, criterion by criterion with evidence", f"{n - 1} applicant columns", shots=shots)
    except Exception as e:
        fail("K11", "compare", "HR Manager", e)


async def case_pool(hr) -> None:
    try:
        t0 = time.time()
        await hr.goto(f"{BASE}/desk/ai-talent-pool?opening={OP2}")
        await hr.wait_for_selector(".tai .rankrow.r4, .tai .note", timeout=90000)
        await settle(hr, 2)
        secs = round(time.time() - t0, 1)
        d = await xcall(hr, "ido_talent_ai.api.talent_pool", {"job_opening": OP2})
        shots = [await snap(hr, "test/K12_talent_pool.png", selector=await visible_page(hr))]
        reasons = sorted({x.get("reason") for x in d.get("excluded", [])})
        ok = len(d.get("suggestions", [])) > 0 and "consent_withdrawn" in reasons and "retention_expired" in reasons
        record("K12", "Talent pool for the Jeddah opening", "HR Manager", ok,
               "rules first, then similarity; withdrawn consent and expired retention excluded with the reason",
               f"{len(d.get('suggestions', []))} suggested, {len(d.get('excluded', []))} excluded ({', '.join(reasons)}); page {secs}s", seconds=secs, shots=shots,
               suggested=len(d.get("suggestions", [])), excluded=len(d.get("excluded", [])), reasons=reasons)
    except Exception as e:
        fail("K12", "talent pool", "HR Manager", e)


async def case_xss(hr, guest) -> None:
    try:
        evil = '<img src=x onerror="window.__xss=1">مختبر'
        a = applicant("2004", applicant_name=evil, email_id=f"t.xss{RERUN}@example.com", national_id=f"100009{NID}203")
        sub = await submit_public(guest, OP1, a, None)
        await wait_final(hr, a["email_id"], 300)
        hits = {}
        for where, url in (("list", f"/desk/job-applicant?job_title={OP1}"), ("form", f"/desk/job-applicant/{a['email_id']}"), ("ranking", f"/desk/ai-ranking?opening={OP1}")):
            await hr.goto(BASE + url)
            await settle(hr, 3)
            hits[where] = await hr.evaluate("({xss: window.__xss === 1, img: !!document.querySelector('img[src=\"x\"]')})")
        await hr.goto(f"{BASE}/desk/job-applicant/{a['email_id']}")
        await settle(hr, 3)
        shots = [await snap(hr, "test/K13_xss_escaped.png", selector=await visible_page(hr))]
        ok = sub.get("ok") and not any(v["xss"] or v["img"] for v in hits.values())
        record("K13", "An applicant name with HTML/JavaScript is shown as text", "Guest → HR Manager", ok,
               "saved; shown as plain text everywhere; no script runs", f"submitted {sub.get('ok')}; " + "; ".join(f"{k}: script {v['xss']}, img {v['img']}" for k, v in hits.items()),
               shots=shots)
    except Exception as e:
        fail("K13", "XSS", "HR Manager", e)


async def case_weights(hr) -> None:
    try:
        prof = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"}))["ai_profile"]
        rk0 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        top0 = [x["applicant"] for x in rk0["ranked"][:5]]
        v0 = rk0["job_version"]
        await hr.goto(f"{BASE}/desk/ai-job-profile/{prof}")
        await settle(hr, 3)
        w0 = await hr.evaluate("Object.fromEntries(cur_frm.doc.criteria.map(c => [c.criterion_key, c.weight]))")
        await hr.evaluate("""(async () => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight += 5; cur_frm.dirty(); await cur_frm.save(); })()""")
        await asyncio.sleep(3)
        blocked = await xcall(hr, "ido_talent_ai.profile.approve", {"name": prof})
        await hr.goto(f"{BASE}/desk/ai-job-profile/{prof}")
        await settle(hr, 3)
        shots = [await snap(hr, "test/K14_weights_105.png", selector=await visible_page(hr))]
        await hr.evaluate("""(async () => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'licence').weight -= 5; cur_frm.dirty(); await cur_frm.save(); })()""")
        await asyncio.sleep(3)
        await hr.goto(f"{BASE}/desk/ai-job-profile/{prof}")
        await settle(hr, 3)
        await hr.evaluate("talent_ai_profile.impact(cur_frm, false)")
        await hr.wait_for_selector(".modal.show .tai table", timeout=90000)
        await asyncio.sleep(2)
        shots.append(await snap(hr, "test/K14_impact_preview.png", selector=".modal.show .modal-content"))
        await hr.evaluate("cur_dialog && cur_dialog.hide()")
        approved = await xcall(hr, "ido_talent_ai.profile.approve", {"name": prof})
        await hr.goto(f"{BASE}/desk/ai-ranking?opening={OP1}")
        await settle(hr, 3)
        shots.append(await snap(hr, "test/K14_ranking_stale.png", selector=await visible_page(hr)))
        t0 = time.time()
        q = await xcall(hr, "ido_talent_ai.api.rescreen_all", {"job_opening": OP1})
        await hr.goto(f"{BASE}/desk/ai-batch?opening={OP1}")
        await settle(hr, 6)
        shots.append(await snap(hr, "test/K14_batch_rescoring.png", selector=await visible_page(hr)))
        while time.time() - t0 < 1500:
            st = await xcall(hr, "ido_talent_ai.api.batch_status", {"job_opening": OP1})
            if not (st.get("applicants") or {}).get("Processing"):
                break
            await asyncio.sleep(5)
        secs = round(time.time() - t0, 1)
        rk = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        top1 = [x["applicant"] for x in rk["ranked"][:5]]
        await hr.goto(f"{BASE}/desk/ai-ranking?opening={OP1}")
        await settle(hr, 3)
        shots.append(await snap(hr, "test/K14_ranking_v2.png", selector=await visible_page(hr)))
        ok = (isinstance(blocked, dict) and "__error__" in blocked and approved.get("version") == v0 + 1 and rk["job_version"] == v0 + 1
              and len(rk["groups"]["stale"]) <= (q.get("skipped") or 0))
        record("K14", "Change the weights, approve version 2, re-score everyone", "HR Manager", ok,
               "105% refused; impact preview; v2 approved; old results stale until re-scored; re-score all",
               f"weights before {w0}; 105% approval {'refused' if isinstance(blocked, dict) and blocked.get('__error__') else 'ACCEPTED'}; v{approved.get('version')} with {approved.get('stale')} stale; "
               f"{q.get('queued')} re-scored in {secs}s, {q.get('skipped')} skipped (consent withdrawn); stale left {len(rk['groups']['stale'])}; top 5 before {top0} after {top1}",
               seconds=secs, shots=shots, rescored=q.get("queued"), top_before=top0, top_after=top1, version=approved.get("version"))
    except Exception as e:
        fail("K14", "weights and versions", "HR Manager", e)


async def case_engine_down(hr, guest) -> None:
    try:
        compose("stop", "api")
        try:
            a = applicant("2017", applicant_name="منصور العتيبي", email_id=f"t.enginedown{RERUN}@example.com", national_id=f"100009{NID}204")
            sub = await submit_public(guest, OP1, a, None, thanks_shot="test/K15_saved_engine_down.png")
            saved = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": a["email_id"], "fieldname": ["name", "ai_status"]})
            failed, t_failed = await wait_value(hr, "Job Applicant", a["email_id"], "ai_status", lambda v: v == "Failed", 900, 5)
            await open_applicant(hr, a["email_id"])
            shots = sub["shots"] + [await snap(hr, "test/K15_failed.png", selector=f"{AI} .tai")]
        finally:
            compose("start", "api")
        for _ in range(60):
            r = await call_status(hr, "/api/method/ido_talent_ai.api.engine_settings")
            if r["status"] == 200:
                break
            await asyncio.sleep(2)
        await open_applicant(hr, a["email_id"])
        t0 = time.time()
        await hr.evaluate("document.querySelector('[data-tai=retry]').click()")
        st, _ = await wait_final(hr, a["email_id"], 300)
        secs = round(time.time() - t0, 1)
        await open_applicant(hr, a["email_id"])
        await hr.evaluate(f"(() => {{ const c = Array.from(document.querySelectorAll('{AI} .tai .card')).find(x => /تقييم الذكاء|AI assessment/.test(x.innerText)); if (c) c.setAttribute('data-tai-head', '1'); }})()")
        shots.append(await snap(hr, "test/K15_after_retry.png", selector=f"{AI} [data-tai-head='1']"))
        ok = sub.get("ok") and saved and failed == "Failed" and st in ("Completed", "Needs Review")
        record("K15", "Engine stopped: apply, then retry", "Guest → HR Manager", ok,
               "the application is saved at once; «فشل» after the retries; «إعادة المحاولة» works when the engine is back",
               f"saved in {sub.get('submit_s')}s while the engine was down; Failed after {t_failed}s; after retry {st} in {secs}s",
               seconds=secs, shots=shots, saved_s=sub.get("submit_s"), failed_after_s=t_failed, retry_s=secs, final=st)
    except Exception as e:
        fail("K15", "engine down", "HR Manager", e)
        compose("start", "api")


# ============================================================================== console (Nadine)
async def run_console(b) -> None:
    page = await new_page(b, "1440", scale=1.5)
    try:
        secs = await login_console(page, ENG["CONSOLE_USER"], ENG["CONSOLE_PASSWORD"])
        shots = []
        for name in ("home", "profile", "list", "ranking", "jobs", "audit", "settings"):
            t0 = time.time()
            await page.evaluate(f"go({json.dumps(name)})")
            await page.wait_for_function("!document.querySelector('#screen .spin')", timeout=60000)
            await settle(page, 1)
            REPORT["timings"].setdefault("console", {})[name] = round(time.time() - t0, 2)
            shots.append(await snap(page, f"test/N01_console_{name}.png", full=True))
        record("N01", "Talent Console: login and the main screens", "Nadine (console)", True, "every screen opens", f"login {secs}s; screens " +
               ", ".join(f"{k} {v}s" for k, v in REPORT["timings"]["console"].items()), seconds=secs, shots=shots)
        # blank height through the console (the public form refuses it; a host system may not)
        await page.evaluate(f"(() => {{ window.__rerun = {json.dumps(RERUN)}; window.__nid = {json.dumps(NID)}; }})()")
        await page.evaluate("go('apply')")
        await page.wait_for_function("!document.querySelector('#screen .spin')", timeout=60000)
        a = applicant("2004")
        t = date.today()
        dob = (t.replace(year=t.year - a["age"]) - timedelta(days=120)).isoformat()
        await page.evaluate("""([a, dob]) => { Object.assign(S.form, {name: 'اختبار طول فارغ', email: 't.console.blankheight' + (window.__rerun || '') + '@example.com', nationality: 'السعودية',
            idNo: '100009' + (window.__nid || '2') + '205', dob, height: '', weight: String(a.weight_kg), consent: true, answers: a.answers}); render(); }""", [a, dob])
        await asyncio.sleep(1.5)
        shots = [await snap(page, "test/K03b_console_form.png", full=True)]
        await page.click("[data-action=submitForm]")
        await page.wait_for_function("S.screen === 'processing'", timeout=60000)
        await page.wait_for_function("!!document.querySelector('[data-action=openApp]:not([disabled])')", timeout=300000)
        await settle(page, 1)
        shots.append(await snap(page, "test/K03b_console_processing.png", full=True))
        await page.click("[data-action=openApp]")
        await settle(page, 2.5)
        shots.append(await snap(page, "test/K03b_console_applicant.png", full=True))
        ref = await page.evaluate("S.sel")
        s = await page.evaluate("fetch('/v1/screenings/' + S.scr, {credentials: 'same-origin'}).then(r => r.json())")
        h = next((c for c in s.get("eligibility_checks", []) if c.get("fact") == "height_cm"), {})
        ok = s.get("eligibility") == "needs_review" and h.get("ok") is None
        record("K03b", "Blank height through the console (a host system that allows it)", "Nadine (console)", ok,
               "eligibility «يحتاج مراجعة» with «?» on the height rule, not «غير مستوفٍ»",
               f"{ref}: eligibility {s.get('eligibility')}; height check {h.get('text_ar')} ok={h.get('ok')}", shots=shots)
        # try a file: the bad-quality scan
        await page.evaluate("go('tryfile')")
        await page.wait_for_selector("#try-file", timeout=30000)
        await page.set_input_files("#try-file", os.path.join(TEST_CVS, "HR-APP-2026-2025-bad.jpg"))
        t0 = time.time()
        await page.click("[data-action=tryRun]")
        await page.wait_for_function("S.tryRes && !document.querySelector('#screen .spin')", timeout=300000)
        await settle(page, 1.5)
        secs = round(time.time() - t0, 1)
        res = await page.evaluate("S.tryRes")
        shot1 = await snap(page, "test/N02_tryfile_bad_image.png", full=True)
        record("N02", "Try a file: the bad-quality scan", "Nadine (console)", res.get("status") in ("ready", "unreadable") or bool(res.get("error")),
               "OCR result with the confidence per line, or «غير مقروء»", f"status {res.get('status')}, method {res.get('extraction_method') or res.get('method')}, confidence {res.get('ocr_confidence')}, {secs}s",
               seconds=secs, shots=[shot1], file="HR-APP-2026-2025-bad.jpg")
    except Exception as e:
        fail("N01", "console", "Nadine (console)", e)
    finally:
        await page.context.close()


# ============================================================================== page timings
async def run_timings(b) -> None:
    """Cold and warm load times of the main pages (seconds until the content is on screen)."""
    out = REPORT["timings"].setdefault("pages", {})
    hr = await new_page(b, "1366")
    await login(hr, "hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])
    pages = [
        ("desk: home", "/desk/ai-recruitment", "!!document.querySelector('.tai-home-grid .tai-home-card, .tai-home-grid a')"),
        ("desk: applicant list", f"/desk/job-applicant?job_title={OP1}", "!!(window.cur_list && cur_list.data && cur_list.data.length)"),
        ("desk: applicant with assessment", f"/desk/job-applicant/{A(2002)}", f"!!document.querySelector('{AI} .tai .card')"),
        ("desk: ranking", f"/desk/ai-ranking?opening={OP1}", "!!document.querySelector('.tai .rankrow')"),
        ("desk: talent pool", f"/desk/ai-talent-pool?opening={OP2}", "!!document.querySelector('.tai .rankrow.r4, .tai .note')"),
        ("desk: AI job profile", "/desk/ai-job-profile", "!!(window.cur_list && cur_list.data)"),
    ]
    for label, url, ready in pages:
        runs = []
        for _ in range(3):
            t0 = time.time()
            await hr.goto(BASE + url)
            await hr.wait_for_function(ready, timeout=120000)
            runs.append(round(time.time() - t0, 2))
        out[label] = {"cold": runs[0], "warm_median": statistics.median(runs[1:]), "runs": runs}
        print("  ", label, out[label], flush=True)
    await hr.context.close()
    g = await new_page(b, "1366")
    for label, url, ready in (("public: jobs", "/jobs", "document.readyState === 'complete'"),
                              ("public: job page", "/jobs/security/security-supervisor-riyadh", "document.readyState === 'complete'"),
                              ("public: application form", f"/ai-apply/new?job_title={OP1}", "!!document.querySelector('#tai-form')")):
        runs = []
        for _ in range(3):
            t0 = time.time()
            await g.goto(BASE + url)
            await g.wait_for_function(ready, timeout=60000)
            runs.append(round(time.time() - t0, 2))
        out[label] = {"cold": runs[0], "warm_median": statistics.median(runs[1:]), "runs": runs}
        print("  ", label, out[label], flush=True)
    await g.context.close()
    m = await new_page(b, "m390")
    t0 = time.time()
    await m.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
    await m.wait_for_selector("#tai-form", timeout=60000)
    out["public: application form (phone 390 px)"] = {"cold": round(time.time() - t0, 2)}
    await m.context.close()
    save()
    slow = {k: v for k, v in out.items() if (v.get("warm_median") or v["cold"]) > 5}
    record("P01", "Page load times", "HR Manager, Guest", not slow, "every main page ready in under 5 s (warm)",
           "; ".join(f"{k}: {v.get('warm_median', v['cold'])}s" for k, v in out.items()))


async def main() -> None:
    os.makedirs(os.path.join(IMG, "roles"), exist_ok=True)
    os.makedirs(os.path.join(IMG, "test"), exist_ok=True)
    REPORT.setdefault("run_started", time.strftime("%Y-%m-%d %H:%M:%S"))
    files = prepare_files()
    async with browser() as b:
        if "roles" in SECTIONS:
            await run_roles(b)
            await run_landing(b)
            await run_other_application(b)
        if "cvtypes" in SECTIONS:
            await run_cvtypes(b, files)
        if "cases" in SECTIONS:
            await run_cases(b)
        if "console" in SECTIONS:
            await run_console(b)
        if "timings" in SECTIONS:
            await run_timings(b)
    t = REPORT["tests"]
    print(f"\n{sum(1 for x in t.values() if x['ok'])}/{len(t)} checks passed; {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
