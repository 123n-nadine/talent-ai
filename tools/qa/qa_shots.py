"""Final QA — screenshots of the screens that changed: the processing stages note when personal data
was redacted from a free answer (1), the applicant list with «—» for a failed screening (2), and the
public form refusing an empty CV file (3). Writes docs/qa/screens/*.png (synthetic data). Part 2
stops the engine's api container for a minute to obtain a failed screening, then starts it again.

    tools/.venv/bin/python tools/qa/qa_shots.py          # all parts
    QA_SHOTS=23 tools/.venv/bin/python tools/qa/qa_shots.py
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, FILL_JS, OP1, applicant, form_values, open_applicant, submit_public  # noqa: E402
from pw import BASE, DEV, ROOT, browser, compact_png, new_page, settle, shot, wait_value, xcall  # noqa: E402

OUT = os.path.join(ROOT, "docs", "qa", "screens")
HR = "hr.manager@example.com"


def compose(*args: str) -> None:
    subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], check=True, capture_output=True)


async def login(page, email: str, password: str) -> None:
    await page.goto(BASE + "/login")
    st = await page.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [email, password])
    assert st == 200
    await page.goto(BASE + "/desk/ai-recruitment")  # desk context: frappe.xcall hangs on the login page after a few calls
    await settle(page, 1.5)


async def snap(page, name: str, selector: str | None = None) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    await shot(page, path, selector=selector)
    compact_png(path)
    print("shot", name, flush=True)


async def main() -> None:
    async with browser() as b:
        hr = await new_page(b, "1366", scale=1.5)
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])
        g = await new_page(b, "1366", scale=1.5)
        parts = os.environ.get("QA_SHOTS", "123")
        # 1 — a free answer with personal data: the answers stage says it was redacted
        if "1" in parts:
            a = applicant("2003", applicant_name="اختبار إخفاء الإجابة الحرة", email_id="qa.redact@example.com", national_id="1000009981")
            a["answers"] = {**a["answers"], "last_job": "مشرف وردية منذ 2019، أتابع 8 حراس — للتواصل 0520202002 أو demo.majed@example.com"}
            sub = await submit_public(g, OP1, a, None)
            assert sub.get("ok"), sub
            name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": a["email_id"], "fieldname": "name"}))["name"]
            await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 300, 2.0)
            await open_applicant(hr, name)
            await hr.evaluate(f"(() => {{ const c = Array.from(document.querySelectorAll('{AI} .tai .card')).find(x => /مراحل المعالجة|Processing/.test(x.innerText)); if (c) c.setAttribute('data-g', '1'); }})()")
            await snap(hr, "01_free_answer_redaction_note", "[data-g='1']")
        # 3 — the public form refuses an empty CV file with a clear sentence (Q6); nothing is sent
        if "3" in parts:
            empty = os.path.join(OUT, "..", "empty-cv.pdf")
            open(empty, "wb").close()
            try:
                a3 = applicant("2003", applicant_name="اختبار ملف فارغ", email_id="qa.emptycv@example.com", national_id="1000009983")
                await g.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
                await g.wait_for_selector("#tai-form", timeout=60000)
                vals, ans = form_values(a3)
                await g.evaluate(FILL_JS, [vals, ans])
                await g.set_input_files("#f-cv", empty)
                await g.click("#tai-form button[type=submit]")
                await g.wait_for_selector(".errors", timeout=30000)
                await asyncio.sleep(1)
                await snap(g, "03_form_empty_cv_refused", ".errors")
            finally:
                os.remove(empty)
        # 2 — a failed screening shows «—» in the applicant list (wide window: the score column is
        # the last one and sits outside a 1366-px list)
        if "2" not in parts:
            await g.context.close()
            await hr.context.close()
            return
        await hr.context.close()
        hr = await new_page(b, "1920", scale=1.5)
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])
        compose("stop", "api")
        try:
            a2 = applicant("2003", applicant_name="اختبار قائمة الفشل", email_id="qa.failedlist@example.com", national_id="1000009982")
            sub2 = await submit_public(g, OP1, a2, None)
            assert sub2.get("ok"), sub2
            name2 = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": a2["email_id"], "fieldname": "name"}))["name"]
            await wait_value(hr, "Job Applicant", name2, "ai_status", lambda v: v == "Failed", 600, 3.0)
        finally:
            compose("start", "api")
        await hr.goto(f"{BASE}/desk/job-applicant?email_id={a2['email_id']}")
        await settle(hr, 3)
        await hr.wait_for_selector(".list-row-container", timeout=60000)
        await asyncio.sleep(1.5)
        await hr.evaluate("""() => { const c = Array.from(document.querySelectorAll('.page-container')).find(e => e.offsetParent !== null); c.setAttribute('data-g', '2'); }""")
        await snap(hr, "02_list_failed_shows_dash", "[data-g='2']")
        for _ in range(60):
            try:
                if urllib.request.urlopen("http://127.0.0.1:18000/health", timeout=3).status == 200:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(2)
        await g.context.close()
        await hr.context.close()


if __name__ == "__main__":
    asyncio.run(main())
