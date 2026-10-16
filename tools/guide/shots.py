"""Screenshots of the guide, taken on the clean demo (run dev-frappe/reset_demo.sh first), cropped
to the element each page explains, at 1.5x for print. Read-only: weights are changed in the form
only to open the impact preview and the form is reloaded without saving; dialogs are closed.

    tools/.venv/bin/python tools/guide/shots.py           # writes docs/guide/images/steps/
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from pw import BASE, CONSOLE, DEV, ENG, ROOT, browser, compact_png, login_console, new_page, settle, shot, xcall  # noqa: E402

OUT = os.path.join(ROOT, "docs", "guide", "images", "steps")
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"
AI = ".frappe-control[data-fieldname=ai_html]"
DONE: list[str] = []


async def snap(page, name: str, selector: str | None = None, full: bool = False, pad: int = 0) -> None:
    path = os.path.join(OUT, name + ".png")
    await shot(page, path, selector=selector, full=full, pad=pad)
    compact_png(path)
    DONE.append(name)
    print("shot", name, flush=True)


async def snap_parts(page, name: str, selector: str, parts: int = 2, cut_at: str | None = None) -> None:
    """The element in `parts` pictures of equal height, each cut where a child (`cut_at` selector)
    starts, so no field or card is split in two."""
    box = await page.locator(selector).first.bounding_box()
    assert box, selector
    tops = []
    if cut_at:
        tops = await page.evaluate("(sel) => Array.from(document.querySelectorAll(sel)).map(e => e.getBoundingClientRect().top + window.scrollY)", f"{selector} {cut_at}")
    y0 = box["y"]
    edges = [y0]
    for i in range(1, parts):
        target = y0 + box["height"] * i / parts
        edges.append(min(tops, key=lambda t: abs(t - target)) if tops else target)
    edges.append(y0 + box["height"])
    for i in range(parts):
        path = os.path.join(OUT, f"{name}_{i + 1}.png")
        await page.screenshot(path=path, full_page=True, clip={"x": box["x"], "y": edges[i], "width": box["width"], "height": edges[i + 1] - edges[i]})
        compact_png(path)
        DONE.append(f"{name}_{i + 1}")
        print("shot", f"{name}_{i + 1}", flush=True)


async def mark(page, js_find: str, attr: str = "data-g") -> str:
    """Tag the element found by `js_find` (a JS expression) so it can be captured."""
    await page.evaluate(f"""() => {{ document.querySelectorAll('[{attr}]').forEach(e => e.removeAttribute('{attr}'));
        const e = ({js_find}); if (e) e.setAttribute('{attr}', '1'); return !!e; }}""")
    return f"[{attr}='1']"


def card(title_re: str, root: str = AI) -> str:
    return f"Array.from(document.querySelectorAll('{root} .tai .card')).find(c => /{title_re}/.test(c.querySelector('h2') ? c.querySelector('h2').innerText : ''))"


async def visible(page) -> str:
    return await mark(page, "Array.from(document.querySelectorAll('.page-container')).find(e => e.offsetParent !== null)", "data-gp")


async def go(page, url: str, wait: str | None = None, extra: float = 2.0) -> None:
    await page.goto(BASE + url)
    await settle(page, extra)
    if wait:
        await page.wait_for_function(wait, timeout=90000)
        await asyncio.sleep(1.2)


async def public(b) -> None:
    g = await new_page(b, "1366", scale=1.5)
    await go(g, "/jobs")
    await snap(g, "S03_jobs", ".page_content, .page-content-wrapper, main, body")
    await go(g, "/jobs/security/security-supervisor-riyadh", "!!document.querySelector('.tai-reqs')")
    await snap(g, "S04_job_page", ".page_content, .page-content-wrapper, main")
    await go(g, f"/ai-apply/new?job_title={OP1}", "!!document.querySelector('#tai-form')")
    sel = await mark(g, "document.querySelector('#tai-form')")
    await g.evaluate("window.scrollTo(0, 0)")
    await snap(g, "S05_form", sel)
    await snap_parts(g, "S05_form", sel, parts=2, cut_at=".field, .chk, button[type=submit]")
    await g.context.close()
    m = await new_page(b, "m390", scale=2)
    await go(m, f"/ai-apply/new?job_title={OP1}", "!!document.querySelector('#tai-form')")
    await snap(m, "S05_form_phone", full=False)
    await m.context.close()


async def desk(b) -> str:
    hr = await new_page(b, "1366", scale=1.5)
    await hr.goto(BASE + "/login")
    await hr.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})})""",
                      ["hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"]])
    prof = (await xcall(await _desk(hr), "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"}))["ai_profile"]
    await go(hr, "/desk/ai-recruitment", "!!document.querySelector('.tai-home-grid')")
    await snap(hr, "S00_home", await visible(hr))
    await go(hr, "/desk/talent-ai", "!!document.querySelector('.tai .mnode, .tai .mapcard')")
    await snap(hr, "S00_cycle_map", await visible(hr))
    # the same two pages in a narrower window: bigger text, two pictures each
    nw = await new_page(b, "1100", scale=1.5)
    await nw.goto(BASE + "/login")
    await nw.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})})""",
                      ["hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"]])
    await go(nw, "/desk/ai-recruitment", "!!document.querySelector('.tai-home-grid')")
    await snap_parts(nw, "S00_home", await visible(nw), parts=2, cut_at=".tai-home-grid > *, .tai-home-grid, .card, h1")
    await nw.context.close()
    # the cycle map needs the full width (its side branches overflow a narrow window): two parts
    await go(hr, "/desk/talent-ai", "!!document.querySelector('.tai .mnode, .tai .mapcard')")
    await snap_parts(hr, "S00_cycle_map", await visible(hr), parts=2, cut_at=".mapcard, .mnode, .card, h1")
    await go(hr, f"/desk/ai-job-profile/{prof}", "window.cur_frm && cur_frm.doc && cur_frm.doc.name")
    await snap(hr, "S01_profile", await visible(hr))
    sel = await mark(hr, "document.querySelector('.frappe-control[data-fieldname=criteria]')")
    await snap(hr, "S01b_criteria", sel)
    await hr.evaluate("(() => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight = 20; c.find(x => x.criterion_key === 'licence').weight = 10; })()")
    await hr.evaluate("talent_ai_profile.impact(cur_frm, false)")
    await hr.wait_for_selector(".modal.show .tai table", timeout=90000)
    await asyncio.sleep(2)
    await snap(hr, "S01c_impact", ".modal.show .modal-content")
    await hr.evaluate("cur_dialog && cur_dialog.hide()")
    await hr.evaluate("(() => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight = 25; talent_ai_profile.help(cur_frm); })()")
    await asyncio.sleep(1.2)
    await snap(hr, "S01d_weights_error", ".frappe-control[data-fieldname=criteria_help]")
    await hr.evaluate("cur_frm.reload_doc()")
    await asyncio.sleep(2)
    await go(hr, f"/desk/job-opening/{OP1}", "window.cur_frm && cur_frm.doc && cur_frm.doc.name")
    sel = await mark(hr, "document.querySelector('.frappe-control[data-fieldname=ai_links]') && document.querySelector('.frappe-control[data-fieldname=ai_links]').closest('.form-section, .section-body')")
    await snap(hr, "S02_opening_ai", sel)
    await snap(hr, "S02_opening", await visible(hr))
    # applicant 2002 (scanned Arabic CV, the worked example)
    await go(hr, "/desk/job-applicant/applicant.2002@example.com", f"!!document.querySelector('{AI} .tai .card')", 3)
    sel = await mark(hr, card("تقييم الذكاء|AI assessment"))
    await snap(hr, "S09_head", sel)
    sel = await mark(hr, card("مراحل المعالجة|Processing"))
    await snap(hr, "S06_stages", sel)
    n = await hr.evaluate(f"document.querySelectorAll('{AI} .stages .pstep').length")
    for i in range(n):
        key = await hr.evaluate(f"(() => {{ const s = document.querySelectorAll('{AI} .stages .pstep')[{i}]; s.setAttribute('data-gs', '{i}'); return {i}; }})()")
        await snap(hr, f"S06_stage_{i + 1:02d}", f"[data-gs='{key}']", pad=6)
    sel = await mark(hr, card("نقاط القوة|Strengths"))
    await snap(hr, "S09b_strengths", sel)
    sel = await mark(hr, card("المعايير والأدلة|Criteria and evidence"))
    await snap(hr, "S09c_evidence", sel)
    sel = await mark(hr, card("نص السيرة|CV text"))
    await snap(hr, "S09d_cvtext", sel)
    sel = await mark(hr, card("قرار الموارد البشرية|HR decision"))
    await snap(hr, "S09f_decision_card", sel)
    sel = await mark(hr, "document.querySelector('.frappe-control[data-fieldname=ai_answers]')")
    await snap(hr, "S05b_answers_grid", sel)
    await hr.evaluate("talent_ai_form.decide(cur_frm, 'Shortlisted')")
    await hr.wait_for_selector(".modal.show [data-fieldname=reason] textarea", timeout=20000)
    await asyncio.sleep(0.8)
    await snap(hr, "S09e_decision_dialog", ".modal.show .modal-content")
    await hr.evaluate("cur_dialog && cur_dialog.hide()")
    await hr.evaluate("talent_ai.openCvAnalysis('applicant.2002@example.com')")
    await hr.wait_for_selector(".modal.show .tai .pageview img", timeout=90000)
    await asyncio.sleep(2)
    await snap(hr, "CV_scan", ".modal.show .modal-content")
    sel = await mark(hr, "Array.from(document.querySelectorAll('.modal.show .tai .card')).find(c => /إخفاء الهوية|Redaction/.test(c.innerText))")
    await snap(hr, "CV_redaction", sel)
    await hr.evaluate("cur_dialog && cur_dialog.hide()")
    for who, name in (("applicant.2001@example.com", "CV_pdf"), ("applicant.2018@example.com", "CV_word")):
        await go(hr, f"/desk/job-applicant/{who}", f"!!document.querySelector('{AI} .tai .card')", 2)
        await hr.evaluate(f"talent_ai.openCvAnalysis({json.dumps(who)})")
        await hr.wait_for_selector(".modal.show .tai .pageview img", timeout=90000)
        await asyncio.sleep(2)
        await snap(hr, name, ".modal.show .modal-content")
        await hr.evaluate("cur_dialog && cur_dialog.hide()")
    # cases on the clean demo (the test run has its own pictures too)
    for who, name in (("applicant.2010@example.com", "X_not_eligible"), ("applicant.2021@example.com", "X_needs_review"), ("applicant.2012@example.com", "X_contradiction"),
                      ("hassan.q.second@example.com", "X_duplicate"), ("applicant.2013@example.com", "X_corrupt")):
        await go(hr, f"/desk/job-applicant/{who}", f"!!document.querySelector('{AI} .tai .card')", 2)
        sel = await mark(hr, card("تقييم الذكاء|AI assessment"))
        await snap(hr, name, sel)
    await go(hr, "/desk/job-applicant/applicant.2012@example.com", f"!!document.querySelector('{AI} .tai .card')", 2)
    sel = await mark(hr, card("المعايير والأدلة|Criteria and evidence"))
    await snap(hr, "X_contradiction_evidence", sel)
    for who, name in (("applicant.2021@example.com", "X_blank"), ("applicant.2006@example.com", "X_zero")):
        await go(hr, f"/desk/job-applicant/{who}", f"!!document.querySelector('{AI} .tai .card')", 2)
        sel = await mark(hr, card("المعايير والأدلة|Criteria and evidence"))
        await snap(hr, name, sel)
    # consent defaults (OPEN_QUESTIONS #20, #21): the paper application waiting for its consent, the
    # dialog (filled, not saved), the one whose consent HR recorded, and the withdrawn applicant
    await go(hr, "/desk/job-applicant/paper.2026@example.com", f"!!document.querySelector('{AI} .tai .note')", 2)
    sel = await mark(hr, f"document.querySelector('{AI} .tai')")
    await snap(hr, "X_paper_awaiting", sel)
    await hr.evaluate("window.__d = talent_ai_form.consent(cur_frm)")
    await hr.wait_for_selector(".modal.show [data-fieldname=source] input", timeout=20000)
    await hr.evaluate("window.__d.set_value('source', 'ورقة موقّعة')")
    await asyncio.sleep(0.8)
    await snap(hr, "X_paper_dialog", ".modal.show .modal-content")
    await hr.evaluate("window.__d.hide()")
    await go(hr, "/desk/job-applicant/paper.2027@example.com", f"!!document.querySelector('{AI} .tai .card')", 2)
    sel = await mark(hr, f"document.querySelector('{AI} .tai')")
    await snap(hr, "X_paper_recorded", sel)
    await hr.evaluate("(() => { const f = cur_frm.fields_dict.ai_facts_section; if (f && f.collapse) f.collapse(false); })()")
    await asyncio.sleep(1.2)
    sel = await mark(hr, "(() => { const f = document.querySelector('.frappe-control[data-fieldname=ai_consent_source]'); return f && f.closest('.form-section'); })()")
    await snap(hr, "X_paper_fields", sel)
    await go(hr, "/desk/job-applicant/applicant.2014@example.com", f"!!document.querySelector('{AI} .tai .note')", 2)
    sel = await mark(hr, f"document.querySelector('{AI} .tai')")
    await snap(hr, "X_withdrawn_applicant", sel)
    await go(hr, f"/desk/ai-ranking?opening={OP1}", "!!document.querySelector('.tai .rankrow')", 2)
    for key, rx in (("X_awaiting_group", "بانتظار الموافقة|Awaiting consent"), ("X_withdrawn_group", "سحب الموافقة|consent withdrawn")):
        sel = await mark(hr, f"(() => {{ const d = Array.from(document.querySelectorAll('.tai details.tai-group')).find(x => /{rx}/i.test(x.querySelector('summary').innerText)); if (d) d.open = true; return d; }})()")
        await asyncio.sleep(0.8)
        await snap(hr, key, sel)
    await go(hr, f"/desk/ai-batch?opening={OP1}", "!!document.querySelector('.tai .page-title')")
    await snap(hr, "S07_batch", await visible(hr))
    await go(hr, f"/desk/job-applicant?job_title={OP1}", "window.cur_list && cur_list.data && cur_list.data.length")
    await snap(hr, "S08_list", await visible(hr))
    await go(hr, f"/desk/ai-ranking?opening={OP1}", "!!document.querySelector('.tai .rankrow')")
    await snap(hr, "S10_ranking", await visible(hr))
    sel = await mark(hr, "Array.from(document.querySelectorAll('.tai .card')).find(c => /كيف يُحسب|How it is computed/.test(c.innerText))")
    await snap(hr, "S10d_how", sel)
    sel = await mark(hr, "Array.from(document.querySelectorAll('.tai .card')).find(c => /الأوزان المعتمدة|Approved weights/.test(c.innerText))")
    await snap(hr, "S10e_weights", sel)
    await hr.evaluate("document.querySelectorAll('.tai details.tai-group').forEach(d => d.open = true)")
    await asyncio.sleep(1)
    sel = await mark(hr, "Array.from(document.querySelectorAll('.tai details.tai-group')).find(d => /غير مستوفين|Not eligible/.test(d.innerText))")
    await snap(hr, "S10f_groups", sel)
    await hr.evaluate("talent_ai.openCompare(['applicant.2001@example.com','applicant.2018@example.com','applicant.2002@example.com'])")
    await hr.wait_for_selector(".modal.show .tai table.cmptable", timeout=90000)
    await asyncio.sleep(2)
    await snap(hr, "S10b_compare", ".modal.show .modal-content")
    await hr.evaluate("cur_dialog && cur_dialog.hide()")
    await go(hr, f"/desk/ai-talent-pool?opening={OP2}", "!!document.querySelector('.tai .rankrow.r4, .tai .note')", 3)
    await snap(hr, "S11_pool", await visible(hr))
    await go(hr, "/desk/ai-recruitment-job", "window.cur_list && cur_list.data")
    await snap(hr, "S12_jobs", await visible(hr))
    first = await hr.evaluate("cur_list.data[0] && cur_list.data[0].name")
    if first:
        await go(hr, f"/desk/ai-recruitment-job/{first}", "window.cur_frm && cur_frm.doc && cur_frm.doc.name")
        await snap(hr, "S12b_job", await visible(hr))
    await go(hr, "/desk/ai-recruitment-settings", "window.cur_frm && cur_frm.doc")
    await asyncio.sleep(2)
    await snap(hr, "S13_settings", await visible(hr))
    await go(hr, "/desk/ai-recruitment-audit-log", "window.cur_list && cur_list.data")
    await snap(hr, "S14_audit", await visible(hr))
    first = await hr.evaluate("cur_list.data[0] && cur_list.data[0].name")
    if first:
        await go(hr, f"/desk/ai-recruitment-audit-log/{first}", "window.cur_frm && cur_frm.doc && cur_frm.doc.name")
        await snap(hr, "S14b_audit_row", await visible(hr))
    # the CSV as Excel shows it (first rows)
    raw = await hr.evaluate(f"fetch('/api/method/ido_talent_ai.api.export_ranking_csv?job_opening={OP1}').then(r => r.text())")
    rows = list(csv.reader(io.StringIO(raw.lstrip("﻿"))))[:9]
    html = "<table>" + "".join("<tr>" + "".join(f"<{'th' if i == 0 else 'td'}>{c}</{'th' if i == 0 else 'td'}>" for c in r[:8]) + "</tr>" for i, r in enumerate(rows)) + "</table>"
    p = await new_page(b, "1366", scale=1.5)
    await p.set_content(f"""<html dir="rtl"><body style="font-family:'IBM Plex Sans Arabic',sans-serif;margin:12px;background:#fff">
      <style>table{{border-collapse:collapse;font-size:13px}}td,th{{border:1px solid #c9d1e0;padding:4px 8px}}th{{background:#e9effc}}</style>{html}</body></html>""")
    await snap(p, "S10c_csv", "table")
    await p.context.close()
    # the worked example's engine reference, for the console pictures
    ref = (await xcall(await _desk(hr), "frappe.client.get_value", {"doctype": "Job Applicant", "filters": "applicant.2002@example.com", "fieldname": "ai_candidate_ref"}))["ai_candidate_ref"]
    await hr.context.close()
    return ref


async def _desk(page):
    await page.goto(BASE + "/desk")
    await page.wait_for_function("window.frappe && frappe.boot && frappe.boot.user", timeout=90000)
    return page


async def console(b, ref: str | None = None) -> None:
    c = await new_page(b, "1440", scale=1.5)
    await c.goto(CONSOLE + "/console/login")
    await settle(c, 1)
    await snap(c, "C_login", ".login, form, body")
    await login_console(c, ENG["CONSOLE_USER"], ENG["CONSOLE_PASSWORD"])
    await c.evaluate(f"(() => {{ S.job = {json.dumps(OP1)}; localStorage.setItem('tc_job', S.job); }})()")
    for name in ("home", "profile", "apply", "list", "ranking", "jobs", "audit", "settings"):
        await c.evaluate(f"go({json.dumps(name)})")
        await c.wait_for_function("!document.querySelector('#screen .spin')", timeout=60000)
        await settle(c, 1.5)
        await snap(c, f"C_{name}", "#screen")
    # one applicant, its processing page and its CV analysis
    await c.evaluate("go('list')")
    await settle(c, 2)
    ref = await c.evaluate("(want) => { const r = Array.from(document.querySelectorAll('[data-action=openApp]')).find(x => want && x.dataset.id === want) || document.querySelector('[data-action=openApp]'); r.click(); return r.dataset.id; }", ref)
    await settle(c, 3)
    await snap(c, "C_applicant", "#screen")
    await c.evaluate("go('processing', {scr: S.scr, sel: S.sel})")
    await settle(c, 2.5)
    await snap(c, "C_processing", "#screen")
    await c.evaluate("go('cv')")
    await settle(c, 4)
    await snap(c, "C_cv", "#screen")
    await c.evaluate("go('tryfile')")
    await settle(c, 1.5)
    await c.set_input_files("#try-file", os.path.join(ROOT, "talent-engine", "data", "cvs", "HR-APP-2026-2019.jpg"))
    await c.click("[data-action=tryRun]")
    await c.wait_for_function("S.tryRes && !document.querySelector('#screen .spin')", timeout=300000)
    await settle(c, 2)
    await snap(c, "C_tryfile", "#screen")
    # developer view: the raw API calls next to the screen (no key, only the session cookie)
    await c.evaluate("(() => { S.dev = true; localStorage.setItem('tc_dev', '1'); go('ranking'); })()")
    await settle(c, 3)
    await snap(c, "C_dev", ".content")
    await c.evaluate("(() => { S.dev = false; localStorage.setItem('tc_dev', '0'); })()")
    await c.context.close()
    d = await new_page(b, "1440", scale=1.25)
    await d.goto(CONSOLE + "/docs")
    await d.wait_for_selector(".swagger-ui .opblock", timeout=60000)
    await asyncio.sleep(2)
    await snap(d, "E_docs", ".swagger-ui")
    print("console ref", ref)


COVERED = {"A1": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09"], "A2": ["C01", "K15"], "A3": ["K04", "K05", "C01"], "A4": ["K07"],
           "A5": ["K09", "K11", "R03"], "A6": ["K15"], "A7": [], "A8": ["R01", "R02", "R08_hr_manager", "R09"]}


async def acceptance(b) -> None:
    """The client's 8 acceptance criteria (docs/ACCEPTANCE_REPORT.md) with the round 2 checks that cover them."""
    import html as _h
    import re as _re

    rows = _re.findall(r"^\| (A\d) \| ([^|]+) \|", open(os.path.join(ROOT, "docs", "ACCEPTANCE_REPORT.md"), encoding="utf-8").read(), _re.M)
    tests = json.load(open(os.path.join(ROOT, "docs", "test-run", "full_test.json"), encoding="utf-8"))["tests"]
    tr = []
    for a, text in rows:
        ids = COVERED.get(a, [])
        ok = all(tests.get(i, {}).get("ok") for i in ids) if ids else None
        state = "✓ نجح" if ok else ("مؤجّل بقرار" if ok is None else "✗")
        tr.append(f"<tr><td class='c'>{a}</td><td>{_h.escape(text.strip())}</td><td class='l'>{' '.join(ids) or '—'}</td><td class='c {'ok' if ok else 'na'}'>{state}</td></tr>")
    page = await new_page(b, "1366", scale=1.5)
    await page.set_content(f"""<html dir="rtl"><head><style>body{{font-family:'IBM Plex Sans Arabic',sans-serif;margin:14px;background:#fff;color:#1f2b47}}
      table{{border-collapse:collapse;width:1100px;font-size:15px}}td,th{{border:1px solid #d9dfeb;padding:8px 10px;vertical-align:top}}th{{background:#e9effc;text-align:start}}
      td.c{{text-align:center;white-space:nowrap}}td.l{{direction:ltr;text-align:left;font-family:monospace;font-size:13px}}.ok{{color:#166c3c;font-weight:700}}.na{{color:#56627c}}</style></head>
      <body><table id="t"><tr><th>المعيار</th><th>نص العميل</th><th>اتغطى بالاختبار</th><th>النتيجة</th></tr>{''.join(tr)}</table></body></html>""")
    await snap(page, "S15_acceptance", "#t")
    await page.context.close()


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    async with browser() as b:
        await public(b)
        ref = await desk(b)
        await console(b, ref)
        await acceptance(b)
    json.dump(sorted(DONE), open(os.path.join(OUT, "_shots.json"), "w"), indent=0)
    print(len(DONE), "shots")


if __name__ == "__main__":
    asyncio.run(main())
