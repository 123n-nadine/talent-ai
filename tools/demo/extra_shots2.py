"""Screens 17 and 18 of the manager's pack, second attempt (see extra_shots.py for 16):
17 the AI-drafted profile already created (AI-JP-…), retaken with no open dropdown;
18 the assessment card with «السيرة قُرئت جزئيًا», triggered naturally by a long fictional CV whose
profile answer overruns the 2500-token cap (checked offline: finish_reason «length» at 2500), so
the engine retries on the first half of the text and raises the flag. No setting is changed.

    tools/.venv/bin/python tools/demo/extra_shots2.py <draft-profile-name> <long-cv.docx>
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, OP1, applicant, open_applicant, submit_public  # noqa: E402
from pw import BASE, DEV, ROOT, browser, compact_png, new_page, settle, shot, wait_value, xcall  # noqa: E402

OUT = os.path.join(ROOT, "demo", "screens")
HR = "hr.manager@example.com"
PARTIAL = {"name": "سعود المطيري", "email": "demo.partial@example.com", "nid": "1000009903"}


async def snap(page, name: str, selector: str | None = None) -> str:
    path = os.path.join(OUT, name + ".png")
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


async def main(draft: str, cv_docx: str) -> None:
    async with browser() as b:
        hr = await new_page(b, "1366", scale=1.5)
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])
        # 17 — the existing AI draft, dropdown closed («-» skips it: a reset removes the draft)
        if draft != "-":
            await hr.goto(f"{BASE}/desk/ai-job-profile/{draft}")
            await settle(hr, 2)
            await hr.wait_for_function("window.cur_frm && cur_frm.doc && cur_frm.doc.name", timeout=60000)
            await asyncio.sleep(1.5)
            await hr.evaluate("document.activeElement && document.activeElement.blur(); document.querySelectorAll('.awesomplete ul').forEach(u => u.setAttribute('hidden', ''))")
            await hr.keyboard.press("Escape")
            await asyncio.sleep(0.8)
            await snap(hr, "17_ai_draft_criteria", await visible(hr))

        # 18 — the long CV
        g = await new_page(b, "1366", scale=1.5)
        a = applicant("2002", applicant_name=PARTIAL["name"], email_id=PARTIAL["email"], national_id=PARTIAL["nid"])
        sub = await submit_public(g, OP1, a, cv_docx)
        await g.context.close()
        assert sub.get("ok"), sub
        name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": PARTIAL["email"], "fieldname": "name"}))["name"]
        st, secs = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 900, 2.0)
        res = await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": name})
        flags = (res.get("result") or {}).get("flags") or []
        print("long CV ->", st, "after", secs, "s, flags", flags, flush=True)
        if "cv_partial_read" in flags:
            await open_applicant(hr, name)
            await hr.evaluate(f"(() => {{ const c = document.querySelector('{AI} .tai .card'); if (c) c.setAttribute('data-g', '1'); }})()")
            await snap(hr, "18_cv_partial_read", "[data-g='1']")
        await hr.context.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
