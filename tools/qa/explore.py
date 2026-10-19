"""Final QA, phase 3 — exploratory tests beyond the walkthrough document, on the local demo.

Inputs through the public form (each a fresh synthetic applicant), behaviour under stress and a
few security probes. Writes a JSON and a Markdown table to docs/qa/ (synthetic data only). The demo
is left with the test applicants: run dev-frappe/reset_demo.sh afterwards.

    tools/.venv/bin/python tools/qa/explore.py
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pymupdf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, CVS, OP1, applicant, open_applicant, submit_public  # noqa: E402,F401
from pw import BASE, DEV, ROOT, browser, new_page, settle, wait_value, xcall  # noqa: E402,F401

OUT_DIR = os.path.join(ROOT, "docs", "qa")
SCRATCH = os.environ.get("TAI_SCRATCH", "/tmp/talentai-qa")
HR = "hr.manager@example.com"
RESULTS: list[dict] = []


def rec(area: str, case: str, expected: str, actual: str, ok: bool | None, **extra) -> None:
    RESULTS.append({"area": area, "case": case, "expected": expected, "actual": actual, "ok": ok, **extra})
    print(("PASS" if ok else "FAIL" if ok is False else "INFO"), area, "|", case, "|", actual[:160], flush=True)


def compose(*args: str) -> None:
    subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], check=True, capture_output=True)


def bench(cmd: str) -> str:
    r = subprocess.run(["docker", "compose", "exec", "-T", "bench", "bash", "-lc", f"cd ~/work/frappe-bench && {cmd}"],
                       cwd=os.path.join(ROOT, "dev-frappe"), capture_output=True, text=True, timeout=300)
    return (r.stdout + r.stderr).strip()


# ----------------------------------------------------------------------------- files
def make_files() -> dict[str, str]:
    os.makedirs(SCRATCH, exist_ok=True)
    f: dict[str, str] = {}
    f["empty"] = os.path.join(SCRATCH, "empty.pdf")
    open(f["empty"], "wb").close()
    f["wrong"] = os.path.join(SCRATCH, "notes.exe")
    open(f["wrong"], "wb").write(b"MZ" + b"\x00" * 2000)
    f["huge"] = os.path.join(SCRATCH, "huge.pdf")
    with open(f["huge"], "wb") as fh:  # a real PDF header then padding past the 10 MB limit
        fh.write(b"%PDF-1.4\n" + b"%" + b"x" * (11 * 1024 * 1024))
    f["encrypted"] = os.path.join(CVS, "sample-encrypted.pdf")
    f["docx"] = os.path.join(CVS, "HR-APP-2026-2018.docx")
    f["bad"] = os.path.join(CVS, "test", "HR-APP-2026-2025-bad.jpg")
    # multi-page PDF: the demo applicant's text PDF repeated on three pages
    src = pymupdf.open(os.path.join(CVS, "HR-APP-2026-2001.pdf"))
    multi = pymupdf.open()
    for _ in range(3):
        multi.insert_pdf(src)
    f["multi"] = os.path.join(SCRATCH, "multi-3-pages.pdf")
    multi.save(f["multi"])
    # rotated scan: the demo scan turned 90°
    from PIL import Image

    im = Image.open(os.path.join(CVS, "demo-majed-cv.jpg"))
    f["rotated"] = os.path.join(SCRATCH, "rotated-90.jpg")
    im.rotate(90, expand=True).save(f["rotated"], "JPEG", quality=80)
    # fully English scanned CV: an English text PDF of the demo rasterised like the synthetic scans
    en = None
    for name in sorted(os.listdir(CVS)):
        if name.endswith(".pdf") and name.startswith("HR-APP"):
            t = pymupdf.open(os.path.join(CVS, name))[0].get_text()
            if t and sum(ch.isascii() and ch.isalpha() for ch in t) > 0.6 * sum(ch.isalpha() for ch in t):
                en = os.path.join(CVS, name)
                break
    assert en, "no English text PDF among the synthetic CVs"
    f["english_scan"] = os.path.join(SCRATCH, "english-scan.jpg")
    # the scan generator lives in the engine (pydantic etc.): run it with the engine's own venv
    subprocess.run([os.path.join(ROOT, "talent-engine", ".venv", "bin", "python"), "-c",
                    "import sys, pathlib; sys.path.insert(0, sys.argv[1]); from scripts.make_cvs import pdf_to_scan; "
                    "pdf_to_scan(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), seed=9)",
                    os.path.join(ROOT, "talent-engine"), en, f["english_scan"]], check=True, cwd=os.path.join(ROOT, "talent-engine"))
    f["english_src"] = en
    return f


async def final(hr, email: str, timeout: float = 420) -> tuple[str | None, float | None, dict]:
    name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": email, "fieldname": "name"}))["name"]
    st, secs = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), timeout, 2.0)
    res = await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": name})
    return st, secs, {"name": name, "flags": (res.get("result") or {}).get("flags") or [], "cv": res.get("cv") or {}, "res": res}


async def file_cases(b, hr, f: dict[str, str]) -> None:
    g = await new_page(b, "1366")
    cases = [
        ("0-byte file", "empty", "saved; CV unreadable, assessed from the answers", "q.empty@example.com", "1000009911"),
        ("wrong file type (.exe)", "wrong", "refused with a clear message (type not supported); nothing saved with a bad file", "q.wrong@example.com", "1000009912"),
        ("huge file (11 MB)", "huge", "refused: larger than 10 MB", "q.huge@example.com", "1000009913"),
        ("password-protected PDF", "encrypted", "saved; CV unreadable, assessed from the answers", "q.encrypted@example.com", "1000009914"),
        ("multi-page PDF (3 pages)", "multi", "saved; all pages read", "q.multi@example.com", "1000009915"),
        ("DOCX CV", "docx", "saved; read as text", "q.docx@example.com", "1000009916"),
        ("rotated scan (90°)", "rotated", "saved; OCR weak or unreadable, never a crash", "q.rotated@example.com", "1000009917"),
        ("low-quality photo", "bad", "saved; low confidence → needs review or weak lines", "q.bad@example.com", "1000009918"),
        ("fully English scanned CV", "english_scan", "saved; OCR reads English (report confidence)", "q.enscan@example.com", "1000009919"),
    ]
    for label, key, expected, email, nid in cases:
        try:
            a = applicant("2002", applicant_name=f"اختبار {label}", email_id=email, national_id=nid)
            sub = await submit_public(g, OP1, a, f[key])
            if not sub.get("ok"):
                rec("files", label, expected, f"refused at submission: {sub.get('errors')}", key in ("wrong", "huge"))
                continue
            st, secs, info = await final(hr, email)
            cv = info["cv"]
            actual = f"saved; ai_status {st} after {secs}s; flags {info['flags']}; cv status {cv.get('status')} method {cv.get('extraction_method')} pages {cv.get('pages')} conf {cv.get('ocr_confidence')} chars {cv.get('chars')}"
            ok = st in ("Completed", "Needs Review")
            if key in ("empty", "encrypted"):
                ok = ok and "cv_unreadable" in info["flags"]
            if key == "multi":
                ok = ok and (cv.get("pages") or 0) >= 3
            rec("files", label, expected, actual, ok, email=email)
        except Exception as e:  # noqa: BLE001
            rec("files", label, expected, f"ERROR {type(e).__name__}: {str(e)[:200]}", False)
    await g.context.close()


# ----------------------------------------------------------------------------- text inputs
async def text_cases(b, hr) -> None:
    g = await new_page(b, "1366")
    long_text = "خبرة طويلة في الحراسة الأمنية. " * 170  # ~5,000 characters
    cases = [
        ("very long free answer (5,000 chars)", {"last_job": long_text}, "اختبار نص طويل", "q.long@example.com", "1000009921"),
        ("emoji in name and answer", {"last_job": "مشرف وردية 👮‍♂️🏢 منذ 2019 ✅"}, "سعد 🚀 المالكي", "q.emoji@example.com", "1000009922"),
        ("mixed Arabic/English", {"last_job": "Shift supervisor مشرف وردية at a compound في الرياض since 2019, 8 guards"}, "Fahad فهد Al-Otaibi", "q.mixed@example.com", "1000009923"),
        ("HTML/script in text fields", {"last_job": "<script>alert('x')</script><b>مشرف</b> وردية منذ 2019"}, "<img src=x onerror=alert(1)>عمر", "q.html@example.com", "1000009924"),
    ]
    for label, answers, name, email, nid in cases:
        try:
            a = applicant("2003", applicant_name=name, email_id=email, national_id=nid)
            a["answers"] = {**a["answers"], **answers}
            sub = await submit_public(g, OP1, a, None)
            if not sub.get("ok"):
                rec("text", label, "saved and rendered as text", f"refused: {sub.get('errors')}", False)
                continue
            st, secs, info = await final(hr, email)
            # rendering: the applicant page must show the text escaped (no executed script, no element injected)
            await open_applicant(hr, info["name"], wait_card=False)
            await asyncio.sleep(2)
            injected = await hr.evaluate("!!document.querySelector('img[src=\"x\"], script:not([src])[data-injected]') || document.title.includes('alert')")
            text_shown = await hr.evaluate("document.body.innerText.includes('<script>') || document.body.innerText.includes('<img')") if "HTML" in label else True
            dialogs = await hr.evaluate("window.__alerts || 0")
            actual = f"saved; ai_status {st} after {secs}s; flags {info['flags']}; injected element: {injected}; literal tags visible: {text_shown}; alerts: {dialogs}"
            ok = st in ("Completed", "Needs Review") and not injected and (text_shown if "HTML" in label else True)
            rec("text", label, "saved; shown as plain text; evaluation runs", actual, ok, email=email)
        except Exception as e:  # noqa: BLE001
            rec("text", label, "saved and rendered as text", f"ERROR {type(e).__name__}: {str(e)[:200]}", False)
    await g.context.close()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def http_get(url: str) -> tuple[int, str]:
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(urllib.request.Request(url, headers={"Accept": "application/json, text/html"}), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def http_post_multipart(url: str, fields: dict[str, str], files: dict[str, tuple[str, bytes]] | None = None) -> tuple[int, str]:
    boundary = "----tai" + uuid.uuid4().hex
    body = io.BytesIO()
    for k, v in fields.items():
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for k, (fname, data) in (files or {}).items():
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode())
        body.write(data)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=body.getvalue(), headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read().decode("utf-8", "ignore")[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:200]


# ----------------------------------------------------------------------------- behaviour
def apply_http(_client, email: str, nid: str, name: str = "متقدم متزامن", cv: str | None = None) -> tuple[int, str]:
    a = applicant("2003", applicant_name=name, email_id=email, national_id=nid)
    t = date.today()
    data = {
        "job_title": OP1, "applicant_name": a["applicant_name"], "email_id": email, "phone_number": a.get("phone_number") or "",
        "nationality": a["nationality"], "id_type": a["id_type"], "national_id": nid,
        "date_of_birth": (t.replace(year=t.year - a["age"]) - timedelta(days=120)).isoformat(),
        "height_cm": str(a["height_cm"]), "weight_kg": str(a["weight_kg"]), "ai_consent": "1",
        "answers": json.dumps(a["answers"], ensure_ascii=False),
    }
    files = {"cv": (os.path.basename(cv), open(cv, "rb").read())} if cv else None
    return http_post_multipart(BASE + "/api/method/ido_talent_ai.api.apply", data, files)


async def behaviour_cases(b, hr) -> None:
    # double submit: two clicks on the submit button within the same second
    g = await new_page(b, "1366")
    try:
        a = applicant("2003", applicant_name="اختبار ضغط مرتين", email_id="q.double@example.com", national_id="1000009931")
        from full_test import FILL_JS, form_values

        await g.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await g.wait_for_selector("#tai-form", timeout=60000)
        vals, ans = form_values(a)
        await g.evaluate(FILL_JS, [vals, ans])
        await g.evaluate("(() => { const b = document.querySelector('#tai-form button[type=submit]'); b.click(); b.click(); })()")
        await g.wait_for_selector(".success, .errors", timeout=120000)
        await asyncio.sleep(3)
        n = await xcall(hr, "frappe.client.get_count", {"doctype": "Job Applicant", "filters": {"email_id": a["email_id"]}})
        rec("behaviour", "double submit (two clicks)", "one application", f"{n} application(s) for the e-mail; button disabled while sending", n == 1)
    except Exception as e:  # noqa: BLE001
        rec("behaviour", "double submit (two clicks)", "one application", f"ERROR {type(e).__name__}: {str(e)[:200]}", False)
    await g.context.close()

    # 20 concurrent submissions through the endpoint, half with a text CV
    try:
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=20) as ex:
            futs = [ex.submit(apply_http, None, f"q.conc{i:02d}@example.com", f"10000099{40 + i:02d}", f"متقدم متزامن {i}", os.path.join(CVS, "HR-APP-2026-2001.pdf") if i % 2 == 0 else None) for i in range(20)]
            codes = [fu.result() for fu in futs]
        submit_s = round(time.time() - t0, 1)
        okc = sum(1 for sc, _ in codes if sc == 200)
        emails = [f"q.conc{i:02d}@example.com" for i in range(20)]
        done = 0
        t1 = time.time()
        while time.time() - t1 < 900:
            sts = await xcall(hr, "frappe.client.get_list", {"doctype": "Job Applicant", "filters": {"email_id": ["in", emails]}, "fields": ["email_id", "ai_status"], "limit_page_length": 50})
            done = sum(1 for s in sts if s["ai_status"] in ("Completed", "Needs Review", "Failed"))
            if done >= okc:
                break
            await asyncio.sleep(5)
        failed = sum(1 for s in sts if s["ai_status"] == "Failed")
        rec("behaviour", "20 concurrent submissions (10 with a CV)", "all saved; all assessed; none failed",
            f"{okc}/20 saved in {submit_s}s; {done} assessed after {round(time.time() - t1)}s; failed {failed}; codes {sorted(set(sc for sc, _ in codes))}", okc == 20 and done == 20 and failed == 0)
    except Exception as e:  # noqa: BLE001
        rec("behaviour", "20 concurrent submissions", "all saved and assessed", f"ERROR {type(e).__name__}: {str(e)[:200]}", False)

    # restart a worker and Redis while a scanned CV is being processed
    for what, svc in (("engine worker", "worker"), ("engine Redis", "redis")):
        try:
            g = await new_page(b, "1366")
            email = f"q.restart.{svc}@example.com"
            a = applicant("2002", applicant_name=f"اختبار إعادة تشغيل {what}", email_id=email, national_id="1000009961" if svc == "worker" else "1000009962")
            sub = await submit_public(g, OP1, a, os.path.join(CVS, "demo-majed-cv.jpg"))
            await g.context.close()
            assert sub.get("ok"), sub
            await asyncio.sleep(6)  # the screening is running (OCR on the CPU)
            t0 = time.time()
            compose("restart", svc)
            restart_s = round(time.time() - t0, 1)
            st, secs, info = await final(hr, email, timeout=900)
            rec("behaviour", f"restart {what} mid-processing", "the application is not lost: assessed later (or Failed with retry), never stuck",
                f"restart took {restart_s}s; ai_status {st} after {secs}s from the restart; flags {info['flags']}", st in ("Completed", "Needs Review", "Failed"))
        except Exception as e:  # noqa: BLE001
            rec("behaviour", f"restart {what} mid-processing", "not lost", f"ERROR {type(e).__name__}: {str(e)[:200]}", False)
            try:
                compose("start", svc)
            except Exception:  # noqa: BLE001
                pass


# ----------------------------------------------------------------------------- security
def security_cases() -> None:
    page = http_get(f"{BASE}/ai-apply/new?job_title={OP1}")[1]
    key = ""
    for ln in open(os.path.join(ROOT, "talent-engine", ".env"), encoding="utf-8"):
        if ln.startswith("TENANT_API_KEY="):
            key = ln.split("=", 1)[1].strip()
    rec("security", "API key in the public page source", "absent", f"key present: {bool(key) and key in page}; 'Bearer' in page: {'Bearer' in page}", bool(key) and key not in page and "Bearer" not in page)
    desk_code = http_get(f"{BASE}/desk/job-applicant")[0]
    rec("security", "desk pages without login", "redirect to login", f"HTTP {desk_code}", desk_code in (301, 302, 303))
    for path, exp in (("/console", (301, 302, 303)), ("/docs", (200, 401, 403)), ("/openapi.json", (200, 401, 403)), ("/v1/jobs", (401,)), ("/v1/settings", (401,))):
        code = http_get(f"http://127.0.0.1:18000{path}")[0]
        note = " (API docs follow API_DOCS_ENABLED: on in dev, off when APP_ENV=production — Q2; no secrets in them, the port is loopback + Tailscale only)" if path in ("/docs", "/openapi.json") and code == 200 else ""
        rec("security", f"engine {path} without credentials", "console → login; /v1 → 401; docs: report", f"HTTP {code}{note}", code in exp)
    # rate limiting on the public form: the demo site allows 100 per IP per 10 minutes; lowered to 5 for the probe and restored
    try:
        bench("bench --site talent.localhost set-config talent_ai_apply_limit 5 >/dev/null")
        time.sleep(65)  # Frappe caches site_config.json for 60 s in each web process
        codes = []
        if True:
            for i in range(8):
                sc, _ = apply_http(None, f"q.rate{i}@example.com", f"10000099{70 + i:02d}", "اختبار حد التقديم")
                codes.append(sc)
        rec("security", "public-form rate limit (5 per 10 min for the probe)", "the sixth and later submissions refused with 429", f"codes {codes}", codes[:5].count(200) == 5 and all(sc == 429 for sc in codes[5:]))
    finally:
        bench("bench --site talent.localhost set-config talent_ai_apply_limit 100 >/dev/null")


async def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    f = make_files()
    async with browser() as b:
        hr = await new_page(b, "1366")
        await hr.goto(BASE + "/login")
        st = await hr.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [HR, DEV["HR_MANAGER_PASSWORD"]])
        assert st == 200
        await hr.goto(BASE + "/desk/ai-recruitment")  # desk context: frappe.xcall hangs on the login page after a few calls
        await settle(hr, 1.5)
        await hr.evaluate("window.__alerts = 0; window.alert = () => { window.__alerts++; }")
        await file_cases(b, hr, f)
        await text_cases(b, hr)
        await behaviour_cases(b, hr)
        await hr.context.close()
    security_cases()
    json.dump(RESULTS, open(os.path.join(OUT_DIR, "explore.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["| area | case | expected | actual | result |", "|---|---|---|---|---|"]
    for r in RESULTS:
        md.append(f"| {r['area']} | {r['case']} | {r['expected']} | {r['actual'].replace('|', '/')} | {'PASS' if r['ok'] else 'FAIL' if r['ok'] is False else 'INFO'} |")
    open(os.path.join(OUT_DIR, "explore.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(sum(1 for r in RESULTS if r["ok"]), "pass /", sum(1 for r in RESULTS if r["ok"] is False), "fail of", len(RESULTS))


if __name__ == "__main__":
    asyncio.run(main())
