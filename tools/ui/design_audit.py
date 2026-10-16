"""Design audit: every Talent AI screen at 1366 / 1440 / 1920 (and 375 / 390 for the public pages):
a tall screenshot and the layout issues found (overlapping or cut text, page overflow, small fonts,
weak contrast, font not loaded).

    tools/.venv/bin/python tools/ui/design_audit.py OUT_DIR [desk,console,public] [1366,1440,1920,m375,m390]
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw import BASE, CONSOLE, DEV, ENG, audit, browser, login_console, login_desk, new_page, save_json, settle, shot  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
PARTS = (sys.argv[2] if len(sys.argv) > 2 else "desk,console,public").split(",")
SIZES = (sys.argv[3] if len(sys.argv) > 3 else "1366,1440,1920").split(",")
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"
AI = ".frappe-control[data-fieldname=ai_html]"
DESK_ROOT = ".tai, .tai-home"


async def desk_screens(page):
    prof = await page.evaluate(f"frappe.xcall('frappe.client.get_value', {{doctype: 'Job Opening', filters: '{OP1}', fieldname: 'ai_profile'}}).then(r => r.ai_profile)")
    return [
        ("home", "/desk/ai-recruitment", None),
        ("cycle_map", "/desk/talent-ai", None),
        ("ai_job_profile", f"/desk/ai-job-profile/{prof}", None),
        ("job_opening", f"/desk/job-opening/{OP1}", None),
        ("applicant_list", f"/desk/job-applicant?job_title={OP1}", None),
        ("applicant_2002_scan", "/desk/job-applicant/applicant.2002@example.com", AI),
        ("applicant_2012_contradiction", "/desk/job-applicant/applicant.2012@example.com", AI),
        ("applicant_duplicate", "/desk/job-applicant/hassan.q.second@example.com", AI),
        ("applicant_2013_cv_rejected", "/desk/job-applicant/applicant.2013@example.com", AI),
        ("applicant_2010_not_eligible", "/desk/job-applicant/applicant.2010@example.com", AI),
        # consent defaults (OPEN_QUESTIONS #20, #21)
        ("applicant_paper_awaiting", "/desk/job-applicant/paper.2026@example.com", AI),
        ("applicant_paper_consent_recorded", "/desk/job-applicant/paper.2027@example.com", AI),
        ("applicant_2014_consent_withdrawn", "/desk/job-applicant/applicant.2014@example.com", AI),
        ("ranking", f"/desk/ai-ranking?opening={OP1}", None),
        ("batch_monitor", f"/desk/ai-batch?opening={OP1}", None),
        ("talent_pool", f"/desk/ai-talent-pool?opening={OP2}", None),
        ("ai_jobs", "/desk/ai-recruitment-job", None),
        ("settings", "/desk/ai-recruitment-settings", None),
        ("audit_log", "/desk/ai-recruitment-audit-log", None),
    ]


DIALOGS = [
    ("dialog_cv_analysis", "/desk/job-applicant/applicant.2002@example.com", "talent_ai.openCvAnalysis('applicant.2002@example.com')", ".modal.show .tai .pageview img"),
    ("dialog_compare", f"/desk/ai-ranking?opening={OP1}", "talent_ai.openCompare(['applicant.2001@example.com','applicant.2018@example.com','applicant.2002@example.com'])", ".modal.show .tai table"),
]


async def run_desk(b, size, report):
    page = await new_page(b, size)
    await login_desk(page, "hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"], via_form=False)
    for name, url, sel in await desk_screens(page):
        await page.goto(BASE + url)
        await settle(page, 2.5)
        if sel:
            await page.wait_for_selector(f"{sel} .card", timeout=60000)
            await settle(page, 1.5)
        res = await audit(page, DESK_ROOT)
        path = await shot(page, os.path.join(OUT, size, f"desk_{name}.png"), full=True)
        report.append({"part": "desk", "size": size, "screen": name, "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
        page.errors.clear()
        print(size, "desk", name, len(res["issues"]), "issues", "plex" if res["fonts"]["plex"] else "NO-PLEX", flush=True)
    for name, url, js, wait in DIALOGS:
        await page.goto(BASE + url)
        await settle(page, 2)
        await page.evaluate(js)
        await page.wait_for_selector(wait, timeout=90000)
        await settle(page, 2)
        res = await audit(page, ".modal.show .tai")
        path = await shot(page, os.path.join(OUT, size, f"desk_{name}.png"), selector=".modal.show .modal-content")
        report.append({"part": "desk", "size": size, "screen": name, "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
        page.errors.clear()
        print(size, "desk", name, len(res["issues"]), "issues", flush=True)
    await page.context.close()


CONSOLE_SCREENS = ["home", "profile", "apply", "list", "ranking", "jobs", "audit", "settings", "cv", "tryfile"]


async def run_console(b, size, report):
    page = await new_page(b, size)
    await page.goto(CONSOLE + "/console/login")
    await settle(page, 1)
    res = await audit(page, "body")
    path = await shot(page, os.path.join(OUT, size, "console_login.png"), full=True)
    report.append({"part": "console", "size": size, "screen": "login", "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
    await login_console(page, ENG["CONSOLE_USER"], ENG["CONSOLE_PASSWORD"])
    for name in CONSOLE_SCREENS:
        await page.evaluate(f"go({json.dumps(name)})")
        await settle(page, 2.5)
        res = await audit(page, "body")
        path = await shot(page, os.path.join(OUT, size, f"console_{name}.png"), full=True)
        report.append({"part": "console", "size": size, "screen": name, "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
        page.errors.clear()
        print(size, "console", name, len(res["issues"]), "issues", flush=True)
    # one applicant page
    await page.evaluate("go('list')")
    await settle(page, 2)
    await page.evaluate("(() => { const b = document.querySelector('[data-action=openApp]'); if (b) b.click(); })()")
    await settle(page, 3)
    res = await audit(page, "body")
    path = await shot(page, os.path.join(OUT, size, "console_applicant.png"), full=True)
    report.append({"part": "console", "size": size, "screen": "applicant", "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
    await page.context.close()


PUBLIC = [("jobs", "/jobs"), ("job_page", "/jobs/security/security-supervisor-riyadh"), ("form_ar", f"/ai-apply/new?job_title={OP1}"), ("form_en", f"/ai-apply/new?job_title={OP1}&lang=en")]


async def run_public(b, size, report):
    page = await new_page(b, size)
    for name, url in PUBLIC:
        await page.goto(BASE + url)
        await settle(page, 2)
        res = await audit(page, "body")
        path = await shot(page, os.path.join(OUT, size, f"public_{name}.png"), full=True)
        report.append({"part": "public", "size": size, "screen": name, "shot": os.path.relpath(path, OUT), **res, "js_errors": list(page.errors)})
        page.errors.clear()
        print(size, "public", name, len(res["issues"]), "issues", flush=True)
    await page.context.close()


async def main():
    report: list[dict] = []
    async with browser() as b:
        for size in SIZES:
            mobile = size.startswith("m")
            if "desk" in PARTS and not mobile:
                await run_desk(b, size, report)
            if "console" in PARTS and not mobile:
                await run_console(b, size, report)
            if "public" in PARTS:
                await run_public(b, size, report)
    save_json(os.path.join(OUT, "audit.json"), report)
    summary: dict[str, int] = {}
    for r in report:
        for i in r["issues"]:
            summary[i["type"]] = summary.get(i["type"], 0) + 1
    print("summary", json.dumps(summary), "screens", len(report))


asyncio.run(main())
