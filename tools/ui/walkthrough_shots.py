"""Screenshots for docs/WALKTHROUGH.md, in the order of the guide (steps 0-15), on the clean demo.

    talent-engine/.venv/bin/python tools/ui/walkthrough_shots.py docs/screenshots

Read-only on the demo except: nothing is saved (weights are changed in the form only to open the
impact preview, then discarded; the reason dialog is cancelled)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acceptance import DEV  # noqa: E402  (reads dev-frappe/.env)
from frappe_ui import Browser  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots")
BASE = "http://127.0.0.1:18050"
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"
AI = ".frappe-control[data-fieldname=ai_html]"


async def settle(b, extra=2.5):
    await b.wait_for("document.readyState === 'complete' && !document.querySelector('.tai .spin')", 60)
    await asyncio.sleep(extra)


async def page(b, name, path, selector=None, before=None, wait=None):
    await b.go(path, 4)
    await settle(b)
    if wait:
        await b.wait_for(wait, 60)
        await asyncio.sleep(1.5)
    if before:
        await b.ev(before)
        await asyncio.sleep(2.5)
    await b.tall_shot(name, selector=selector)
    print("shot", name)


async def dialog(b, name, js, wait=".modal.show .tai"):
    err = await b.ev(js)
    if not await b.wait_for(f"!!document.querySelector('{wait}')", 90):
        raise RuntimeError(f"{name}: dialog did not open ({err})")
    await asyncio.sleep(2.5)
    await b.shot(name, selector=".modal.show .modal-content")
    await b.ev("cur_dialog && cur_dialog.hide(); document.querySelectorAll('.modal.show .btn-modal-close').forEach(x => x.click())")
    await asyncio.sleep(1)
    print("shot", name)


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with Browser(BASE, OUT, port=18093, height=1300) as guest:
        await page(guest, "03_jobs_portal", "/jobs")
        await page(guest, "04_job_page", "/jobs/security/security-supervisor-riyadh", wait="!!document.querySelector('.tai-reqs')")
        await page(guest, "05_form_ar", f"/ai-apply/new?job_title={OP1}")
        await guest.ev("document.querySelector('[data-lang=en]').click()")
        await asyncio.sleep(1.5)
        await guest.tall_shot("05_form_en")
        print("shot 05_form_en")
    async with Browser(BASE, OUT, port=18094, height=1300) as hr:
        await hr.login("hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])
        prof = (await hr.ev(f"frappe.xcall('frappe.client.get_value', {{doctype: 'Job Opening', filters: '{OP1}', fieldname: 'ai_profile'}}).then(r => r.ai_profile)"))
        await page(hr, "00_cycle_map", "/desk/talent-ai")
        await page(hr, "01_ai_job_profile", f"/desk/ai-job-profile/{prof}")
        await hr.ev("(() => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight = 20; c.find(x => x.criterion_key === 'licence').weight = 10; })()")
        await dialog(hr, "01b_impact_preview", "talent_ai_profile.impact(cur_frm, false)", ".modal.show .tai table")
        await hr.ev("(() => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight = 25; })()")
        await hr.ev("talent_ai_profile.help(cur_frm)")
        await asyncio.sleep(1)
        await hr.tall_shot("01c_weights_not_100", selector=".frappe-control[data-fieldname=criteria_help]")
        await hr.ev("cur_frm.reload_doc()")
        await asyncio.sleep(2)
        await page(hr, "02_job_opening", f"/desk/job-opening/{OP1}")
        await page(hr, "06_applicant_stages", "/desk/job-applicant/applicant.2002@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .stages')")
        await dialog(hr, "06b_cv_analysis_scan", "talent_ai.openCvAnalysis('applicant.2002@example.com')", ".modal.show .tai .pageview img")
        await hr.go("/desk/job-applicant/applicant.2001@example.com", 5)
        await settle(hr)
        await dialog(hr, "06c_cv_analysis_pdf", "talent_ai.openCvAnalysis('applicant.2001@example.com')", ".modal.show .tai .pageview img")
        await page(hr, "07_batch_monitor", f"/desk/ai-batch?opening={OP1}")
        await page(hr, "08_applicant_list", f"/desk/job-applicant?job_title={OP1}")
        await page(hr, "09_applicant_ai_section", "/desk/job-applicant/applicant.2002@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .card')")
        await hr.ev(f"document.querySelector('{AI} [data-tai=decide][data-status=Rejected]').click()")
        await hr.wait_for("!!document.querySelector('.modal.show textarea')", 30)
        await asyncio.sleep(1)
        await hr.shot("09e_decision_reason", selector=".modal.show .modal-content")
        await hr.ev("cur_dialog && cur_dialog.hide()")
        print("shot 09e_decision_reason")
        await page(hr, "09b_contradiction", "/desk/job-applicant/applicant.2012@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .card')")
        await page(hr, "09c_duplicate", "/desk/job-applicant/hassan.q.second@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .card')")
        await page(hr, "09f_not_eligible", "/desk/job-applicant/applicant.2010@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .card')")
        await page(hr, "09g_cv_rejected", "/desk/job-applicant/applicant.2013@example.com", selector=AI, wait=f"!!document.querySelector('{AI} .card')")
        await page(hr, "10_ranking", f"/desk/ai-ranking?opening={OP1}",
                   before="document.querySelectorAll('.tai details.tai-group').forEach(d => d.open = true)")
        await hr.go(f"/desk/ai-ranking?opening={OP1}", 5)
        await settle(hr)
        await dialog(hr, "10c_compare", "talent_ai.openCompare(['applicant.2001@example.com', 'applicant.2018@example.com', 'applicant.2002@example.com'])", ".modal.show .tai table.cmptable")
        await page(hr, "11_talent_pool", f"/desk/ai-talent-pool?opening={OP2}", wait="!!document.querySelector('.tai .rankrow') || !!document.querySelector('.tai .note.danger')")
        await page(hr, "12_ai_jobs", "/desk/ai-recruitment-job")
        await page(hr, "13_settings", "/desk/ai-recruitment-settings", wait="!!document.querySelector('[data-fieldname=engine_status] .card')")
        await page(hr, "14_audit_log", "/desk/ai-recruitment-audit-log")
        print("JS errors:", len(hr.errors), hr.errors[:3])


asyncio.run(main())
