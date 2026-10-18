"""Three extra screens for the manager's pack, taken like the rehearsal (same browser, same size):
16 the public form in English, 17 an AI-drafted criteria profile (not approved), 18 the assessment
card with «السيرة قُرئت جزئيًا». The third needs the shorter retry to happen: the engine's answer
budget is squeezed for one applicant through LLM_MAX_MODEL_LEN in talent-engine/.env (backed up and
restored, api and workers recreated twice). Run from a clean reset and reset again afterwards.

    tools/.venv/bin/python tools/demo/extra_shots.py
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, CVS, OP1, applicant, open_applicant, submit_public  # noqa: E402
from pw import BASE, DEV, ROOT, browser, compact_png, new_page, settle, shot, wait_value, xcall  # noqa: E402

OUT = os.path.join(ROOT, "demo", "screens")
ENV = os.path.join(ROOT, "talent-engine", ".env")
HR = "hr.manager@example.com"
PARTIAL = {"name": "سعود المطيري", "email": "demo.partial@example.com", "nid": "1000009903"}


async def snap(page, name: str, selector: str | None = None, clip: dict | None = None) -> str:
    path = os.path.join(OUT, name + ".png")
    if clip:
        await page.screenshot(path=path, full_page=True, clip=clip)
    else:
        await shot(page, path, selector=selector)
    compact_png(path)
    print("shot", name, flush=True)
    return path


async def visible(page) -> str:
    await page.evaluate("""() => { document.querySelectorAll('[data-tai-shot]').forEach(e => e.removeAttribute('data-tai-shot'));
      const c = Array.from(document.querySelectorAll('.page-container')).find(e => e.offsetParent !== null) || document.body;
      c.setAttribute('data-tai-shot', '1'); }""")
    return '[data-tai-shot="1"]'


async def login(page, email: str, password: str) -> None:
    await page.goto(BASE + "/login")
    st = await page.evaluate(
        """([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [email, password])
    assert st == 200, f"login {email}: HTTP {st}"


def compose(*args: str) -> None:
    subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], check=True, capture_output=True)


def recreate_engine() -> None:
    compose("up", "-d", "--no-build", "--no-deps", "--scale", "worker=4", "api", "worker")
    for _ in range(90):
        try:
            if urllib.request.urlopen("http://127.0.0.1:18000/health", timeout=3).status == 200:
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    raise RuntimeError("engine api did not come back")


def set_budget(value: int | None) -> None:
    """LLM_MAX_MODEL_LEN in talent-engine/.env (None = the backed-up original), then recreate."""
    backup = ENV + ".extra-shots.bak"
    if value is None:
        if os.path.exists(backup):
            shutil.copy2(backup, ENV)
            os.remove(backup)
    else:
        if not os.path.exists(backup):
            shutil.copy2(ENV, backup)
        lines = [ln for ln in open(backup, encoding="utf-8").read().splitlines() if not ln.startswith("LLM_MAX_MODEL_LEN=")]
        lines.append(f"LLM_MAX_MODEL_LEN={value}   # TEMPORARY (extra_shots.py): squeezes the answer budget to force the shorter retry")
        open(ENV, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        os.chmod(ENV, 0o600)
    recreate_engine()


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    async with browser() as b:
        # 16 — the public form in English, from the top to the screening questions
        g = await new_page(b, "1366", scale=1.5)
        await g.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await g.wait_for_selector("#tai-form", timeout=60000)
        await g.click('[data-lang="en"]')
        await asyncio.sleep(1.5)
        await g.wait_for_selector("#tai-form", timeout=60000)
        box = await g.locator("#tai-form").bounding_box()
        q = await g.locator("#tai-form .sechead >> nth=1").bounding_box()
        h = await g.evaluate("document.documentElement.scrollHeight")
        await g.set_viewport_size({"width": 1366, "height": min(int(h), 14000)})
        await asyncio.sleep(0.8)
        box = await g.locator("#tai-form").bounding_box()
        q = await g.locator("#tai-form .sechead >> nth=1").bounding_box()
        await snap(g, "16_form_english", clip={"x": box["x"] - 8, "y": box["y"] - 8, "width": box["width"] + 16, "height": q["y"] + q["height"] + 8 - (box["y"] - 8)})
        await g.context.close()

        # 17 — a new criteria profile drafted by the AI (left as a draft, never approved)
        hr = await new_page(b, "1366", scale=1.5)
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])
        await hr.goto(BASE + "/desk/ai-job-profile/new")
        await settle(hr, 2)
        await hr.wait_for_function("window.cur_frm && cur_frm.doc && cur_frm.doc.doctype === 'AI Job Profile'", timeout=60000)
        await hr.evaluate("cur_frm.set_value('title', 'حارس أمن — الدمام')")
        await hr.evaluate("cur_frm.save()")
        await hr.wait_for_function("cur_frm.doc && !cur_frm.doc.__islocal && !cur_frm.is_dirty()", timeout=60000)
        await asyncio.sleep(1)
        await hr.evaluate("talent_ai_profile.ai_draft(cur_frm)")
        await hr.wait_for_function("cur_frm.doc && cur_frm.doc.is_ai_draft == 1 && (cur_frm.doc.criteria || []).length > 0", timeout=300000)
        await settle(hr, 3)
        await hr.wait_for_function("!document.querySelector('.freeze-message, #freeze')", timeout=60000)
        await asyncio.sleep(1.5)
        await snap(hr, "17_ai_draft_criteria", await visible(hr))
        draft_name = await hr.evaluate("cur_frm.doc.name")
        print("draft profile", draft_name, "criteria", await hr.evaluate("(cur_frm.doc.criteria || []).length"), flush=True)

        # 18 — the assessment card of an applicant whose CV was read partially
        got = False
        try:
            for budget in (1450, 1550, 1350):
                set_budget(budget)
                email = f"{budget}.{PARTIAL['email']}"
                a = applicant("2002", applicant_name=PARTIAL["name"], email_id=email, national_id=str(int(PARTIAL["nid"]) + budget))
                g2 = await new_page(b, "1366", scale=1.5)
                sub = await submit_public(g2, OP1, a, os.path.join(CVS, "demo-majed-cv.jpg"))
                await g2.context.close()
                assert sub.get("ok"), sub
                name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": email, "fieldname": "name"}))["name"]
                st, secs = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 600, 1.0)
                res = await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": name})
                flags = (res.get("result") or {}).get("flags") or []
                print("budget", budget, "->", st, "after", secs, "s, flags", flags, flush=True)
                if "cv_partial_read" in flags:
                    await open_applicant(hr, name)
                    await hr.evaluate(f"(() => {{ const c = document.querySelector('{AI} .tai .card'); if (c) c.setAttribute('data-g', '1'); }})()")
                    await snap(hr, "18_cv_partial_read", "[data-g='1']")
                    got = True
                    break
        finally:
            set_budget(None)
        await hr.context.close()
    print("done; partial-read screen:", got, "| .env restored:", not os.path.exists(ENV + ".extra-shots.bak"))


if __name__ == "__main__":
    asyncio.run(main())
