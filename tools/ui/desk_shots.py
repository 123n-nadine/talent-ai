"""Log in as an HR user and render the Talent AI desk screens: JS errors, overflow, disclaimer, screenshots."""
import asyncio, json, sys
sys.path.insert(0, sys.path[0])
from frappe_ui import Browser

BASE, SHOTS, USER, PW = sys.argv[1:5]
ONLY = set(sys.argv[5].split(",")) if len(sys.argv) > 5 and sys.argv[5] else set()
OPENING = "HR-OPN-2026-0001"


async def main():
    async with Browser(BASE, SHOTS, port=18093, height=1100) as b:
        print("login:", await b.login(USER, PW))

        async def page(name, path, wait_expr="!document.querySelector('.tai .spin') && document.readyState === 'complete'", settle=2.5, full=True, after=None):
            if ONLY and name not in ONLY:
                return
            n0 = len(b.errors)
            await b.go(path, 3)
            await b.wait_for(wait_expr, 60)
            await asyncio.sleep(settle)
            if after:
                await b.ev(after)
                await asyncio.sleep(2.5)
            txt = await b.ev("document.querySelector('.page-container:not([style*=\"display: none\"]) .layout-main, .page-container .layout-main, body')?.innerText || ''") or ""
            ov = await b.overflow()
            disc = "ليست احتمال نجاح" in txt or "not a probability" in txt
            dlg = await b.ev("!!document.querySelector('.modal.show .tai')")
            if dlg:
                await b.tall_shot(name + "_dialog", selector=".modal.show .modal-content")
            else:
                await b.tall_shot(name)
                if await b.ev("!!document.querySelector('.frappe-control[data-fieldname=ai_html] .tai .card')"):
                    await b.tall_shot(name + "_ai", selector=".frappe-control[data-fieldname=ai_html]")
            errs = b.errors[n0:]
            print(f"{name:<26} chars={len(txt):>6} disclaimer={disc!s:<5} docW={ov['docW']} W={ov['W']} errors={len(errs)} {errs[:2] if errs else ''}")

        await page("00_cycle_map", "/desk/talent-ai")
        await page("01_profile", "/desk/ai-job-profile/" + (await b.ev("frappe.xcall(\"frappe.client.get_value\", {doctype: \"Job Opening\", filters: \"" + OPENING + "\", fieldname: \"ai_profile\"}).then(r => r.ai_profile)")))
        await page("02_opening", f"/desk/job-opening/{OPENING}")
        await page("07_batch", f"/desk/ai-batch?opening={OPENING}")
        await page("08_list", f"/desk/job-applicant?job_title={OPENING}")
        await page("09_applicant_2002", "/desk/job-applicant/applicant.2002@example.com")
        await page("09a_applicant_2012_contradiction", "/desk/job-applicant/applicant.2012@example.com")
        await page("09c_applicant_2016_duplicate", "/desk/job-applicant/hassan.q.second@example.com")
        await page("09d_applicant_2013_cv_rejected", "/desk/job-applicant/applicant.2013@example.com")
        await page("09e_applicant_2010_not_eligible", "/desk/job-applicant/applicant.2010@example.com")
        await page("09f_applicant_2021_needs_review", "/desk/job-applicant/applicant.2021@example.com")
        await page("06_cv_analysis_2002", "/desk/job-applicant/applicant.2002@example.com", after="talent_ai.openCvAnalysis('applicant.2002@example.com')")
        await page("10_ranking", f"/desk/ai-ranking?opening={OPENING}")
        await page("12_jobs", "/desk/ai-recruitment-job")
        await page("13_settings", "/desk/ai-recruitment-settings")
        await page("14_audit", "/desk/ai-recruitment-audit-log")
        print("total JS errors:", len(b.errors))
        for e in b.errors[:12]:
            print("  ", e)


asyncio.run(main())
