"""Phase 7: the client's 8 acceptance criteria (+ the guide's continuation steps) checked on the local
bench in a real browser, as the real users. Writes screenshots and a JSON report.

    talent-engine/.venv/bin/python tools/ui/acceptance.py OUT_DIR

Reads passwords from dev-frappe/.env and the engine key from talent-engine/.env. It changes the demo
data (decisions, a new profile version, an engine outage); run dev-frappe/reset_demo.sh afterwards
to get the clean demo back. Synthetic data only."""

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frappe_ui import Browser  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "/tmp/acceptance")
BASE = "http://127.0.0.1:18050"
ENGINE = "http://127.0.0.1:18000"
OP1, OP2 = "HR-OPN-2026-0001", "HR-OPN-2026-0002"
CVS = os.path.join(ROOT, "talent-engine", "data", "cvs")


def env(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.rstrip("\n").split("=", 1)
            out[k.strip()] = v.strip()
    return out


DEV = env(os.path.join(ROOT, "dev-frappe", ".env"))
KEY = env(os.path.join(ROOT, "talent-engine", ".env"))["TENANT_API_KEY"]
REPORT = {"run_at": time.strftime("%Y-%m-%d %H:%M:%S"), "checks": {}}


def record(key, ok, **details):
    REPORT["checks"][key] = {"ok": bool(ok), **details}
    print(f"{'PASS' if ok else 'FAIL'}  {key}  {json.dumps(details, ensure_ascii=False)[:300]}", flush=True)
    with open(os.path.join(OUT, "acceptance.json"), "w", encoding="utf-8") as f:
        json.dump(REPORT, f, ensure_ascii=False, indent=1)


def eng(path, method="GET", body=None):
    req = urllib.request.Request(ENGINE + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", f"Bearer {KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def compose(*args):
    return subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], cwd=os.path.join(ROOT, "talent-engine"),
                          capture_output=True, text=True, env={**os.environ, "BUILDX_BUILDER": "default"})


def squash(x) -> str:
    return "".join(str(x).split())


def blank(v) -> bool:
    return v is None or v == "" or v == []


def same(evidence, answer) -> bool:
    """The evidence cites the stored answer (numbers, options or every selected option)."""
    e = squash(evidence)
    if isinstance(answer, list):
        return all(squash(a) in e for a in answer)
    a = squash(answer)
    try:
        return float(e) == float(a)
    except ValueError:
        return a in e or e in a


async def xcall(b, method, args=None):
    return await b.ev(f"frappe.xcall({json.dumps(method)}, {json.dumps(args or {}, ensure_ascii=False)}).then(r => r, e => ({{__error__: String(e && (e.message || e))}}))")


async def wait_value(b, doctype, name, field, ok, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = await xcall(b, "frappe.client.get_value", {"doctype": doctype, "filters": name, "fieldname": field})
        val = (v or {}).get(field) if isinstance(v, dict) else None
        if ok(val):
            return val
        await asyncio.sleep(3)
    return None


async def fill_form(b, a, cv_path=None):
    t = date.today()
    dob = (t.replace(year=t.year - a["age"]) - timedelta(days=120)).isoformat()
    vals = {k: a.get(k) or "" for k in ("applicant_name", "email_id", "phone_number", "nationality", "id_type", "national_id", "height_cm", "weight_kg")}
    vals["date_of_birth"] = dob
    await b.ev(f"""(() => {{ const v = {json.dumps(vals, ensure_ascii=False)}; const ans = {json.dumps(a['answers'], ensure_ascii=False)};
      const f = document.getElementById('tai-form');
      for (const [k, x] of Object.entries(v)) {{ const el = f.querySelector('[name="' + k + '"]'); if (el) el.value = x; }}
      for (const [k, x] of Object.entries(ans)) {{
        if (Array.isArray(x)) {{ f.querySelectorAll('[data-qm="' + k + '"]').forEach(c => c.checked = x.includes(c.value)); continue; }}
        const el = f.querySelector('[data-q="' + k + '"]'); if (el) el.value = x === null ? '' : String(x); }}
      document.getElementById('f-consent').checked = true; }})()""")
    if cv_path:
        import base64
        b64 = base64.b64encode(open(cv_path, "rb").read()).decode()
        name = os.path.basename(cv_path)
        await b.ev(f"""(() => {{ const bin = atob('{b64}'); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
           const dt = new DataTransfer(); dt.items.add(new File([u], {json.dumps(name)}, {{type: 'application/pdf'}})); document.getElementById('f-cv').files = dt.files; }})()""")


async def submit_form(b, opening, a, shot_prefix, cv_path=None):
    await b.go(f"/ai-apply/new?job_title={opening}", 4)
    await fill_form(b, a, cv_path)
    await b.tall_shot(shot_prefix + "_filled")
    t0 = time.time()
    await b.ev("document.querySelector('#tai-form button[type=submit]').click()")
    ok = await b.wait_for("!!document.querySelector('.success')", 120)
    secs = round(time.time() - t0, 1)
    await b.tall_shot(shot_prefix + "_thanks")
    return ok, secs


def applicant(key, **over):
    data = json.load(open(os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai", "scripts", "demo_data.json"), encoding="utf-8"))
    a = dict(next(x for x in data["applicants"] if x["key"].endswith(key)))
    a.update(over)
    return a


async def main():
    os.makedirs(OUT, exist_ok=True)
    # ------------------------------------------------------------------ HR Manager session
    async with Browser(BASE, OUT, port=18095, height=1100) as hr:
        await hr.login("hr.manager@example.com", DEV["HR_MANAGER_PASSWORD"])

        # A1 + A2: a new application through the public form, then live status on the open form
        async with Browser(BASE, OUT, port=18096, height=1400) as guest:
            a = applicant("2014", applicant_name="سامي القحطاني", email_id="a1.sami@example.com", national_id="1000099001")
            ok, secs = await submit_form(guest, OP1, a, "A1_form", os.path.join(CVS, "HR-APP-2026-2014.pdf"))
        doc = await xcall(hr, "frappe.client.get", {"doctype": "Job Applicant", "name": "a1.sami@example.com"})
        n_q = len((await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": "a1.sami@example.com"}))["questions"])
        answers = doc.get("ai_answers") or []
        record("A1_application_linked_with_all_answers", ok and doc.get("job_title") == OP1 and len(answers) == n_q,
               saved_in_s=secs, job_title=doc.get("job_title"), answers=len(answers), questions=n_q,
               cv_attached=bool(doc.get("resume_attachment")))
        await hr.go("/desk/job-applicant/a1.sami@example.com", 5)
        await hr.ev("window.__tai_marker = 'no-reload'")
        seen = [await hr.ev("(cur_frm && cur_frm.doc.ai_status) || ''")]
        await hr.tall_shot("A2_processing")
        t0 = time.time()
        while time.time() - t0 < 240:
            st = await hr.ev("(cur_frm && cur_frm.doc.ai_status) || ''")
            if st and st != seen[-1]:
                seen.append(st)
            if st in ("Completed", "Needs Review", "Failed"):
                break
            await asyncio.sleep(2)
        marker = await hr.ev("window.__tai_marker || ''")
        await asyncio.sleep(3)
        await hr.tall_shot("A2_completed")
        record("A2_status_updates_live", seen[-1] in ("Completed", "Needs Review") and marker == "no-reload",
               statuses=seen, page_not_reloaded=marker == "no-reload", seconds=round(time.time() - t0, 1))

        # A3: every level above 0 carries verified evidence (engine data for the whole opening)
        rk = eng(f"/v1/jobs/{OP1}/ranking")
        sids = [x["screening_id"] for x in rk["ranked"]] + [x["screening_id"] for g in rk["groups"].values() for x in g]
        n_lvl = n_ok = n_cv = 0
        bad = []
        for sid in sids:
            s = eng(f"/v1/screenings/{sid}")
            cand = eng(f"/v1/candidates/{s['candidate_ref']}")
            text = ((s.get("cv") or {}).get("redacted_text") or "")
            for c in s["criteria"]:
                if (c.get("level") or 0) <= 0:
                    continue
                n_lvl += 1
                ev = c.get("evidence") or ""
                if c["source"] == "form_field":
                    ans = cand["answers"].get(c.get("field"))
                    good = bool(ev) and not blank(ans) and same(ev, ans)
                elif c["source"] == "cv_quote":
                    n_cv += 1
                    good = bool(ev) and squash(ev.split(" | ")[0])[:30] in squash(text)
                else:
                    good = c["source"] == "hr_override"
                n_ok += good
                if not good:
                    bad.append({"screening": sid, "criterion": c["key"], "source": c["source"], "evidence": ev[:60]})
        record("A3_every_level_has_evidence", n_lvl > 0 and n_ok == n_lvl, levels_above_0=n_lvl, with_verified_evidence=n_ok,
               from_cv=n_cv, problems=bad[:5], screenings=len(sids))

        # A4: edit an answer after evaluation -> stale, out of the ranking; re-score -> back
        await hr.go("/desk/job-applicant/applicant.2004@example.com", 5)
        await hr.ev("""(async () => { const r = cur_frm.doc.ai_answers.find(x => x.question_key === 'years_sup'); r.answer = '6'; cur_frm.dirty(); await cur_frm.save(); })()""")
        await asyncio.sleep(5)
        stale = await wait_value(hr, "Job Applicant", "applicant.2004@example.com", "ai_stale", lambda v: v == 1, 30)
        await hr.go("/desk/job-applicant/applicant.2004@example.com", 6)
        banner = await hr.ev("document.querySelector('[data-fieldname=ai_html]').innerText.includes('لا تعكس آخر تعديل')")
        await hr.tall_shot("A4_stale_banner_ai", selector=".frappe-control[data-fieldname=ai_html]")
        rk = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        in_stale = any(x.get("applicant") == "applicant.2004@example.com" for x in rk["groups"]["stale"])
        in_ranked = any(x.get("applicant") == "applicant.2004@example.com" for x in rk["ranked"])
        await hr.ev("document.querySelector('[data-tai=rescreen]').click()")
        await asyncio.sleep(1)
        await hr.ev("document.querySelector('.modal.show .btn-primary') && document.querySelector('.modal.show .btn-primary').click()")
        back = await wait_value(hr, "Job Applicant", "applicant.2004@example.com", "ai_stale", lambda v: v == 0, 240)
        await wait_value(hr, "Job Applicant", "applicant.2004@example.com", "ai_status", lambda v: v in ("Completed", "Needs Review"), 240)
        score = await wait_value(hr, "Job Applicant", "applicant.2004@example.com", "ai_score", lambda v: v is not None, 30)
        rk2 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        ranked_again = any(x.get("applicant") == "applicant.2004@example.com" for x in rk2["ranked"])
        record("A4_edit_makes_result_stale", stale == 1 and banner and in_stale and not in_ranked and back == 0 and ranked_again,
               stale_flag=stale, banner=banner, in_stale_group=in_stale, ranked_while_stale=in_ranked, rescored=back == 0,
               new_score=score, ranked_again=ranked_again)

        # A5: openings never mixed; AI never changes the status; decisions need a reason
        async with Browser(BASE, OUT, port=18096, height=1400) as guest:
            for k, email, nid in (("2018", "jeddah.1@example.com", "1000099101"), ("2019", "jeddah.2@example.com", "1000099102")):
                await submit_form(guest, OP2, applicant(k, email_id=email, national_id=nid), f"A5_jeddah_{k}")
        for email in ("jeddah.1@example.com", "jeddah.2@example.com"):
            await wait_value(hr, "Job Applicant", email, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 300)
        r1 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        r2 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP2})
        names1 = {x.get("applicant") for x in r1["ranked"]} | {x.get("applicant") for g in r1["groups"].values() for x in g}
        names2 = {x.get("applicant") for x in r2["ranked"]} | {x.get("applicant") for g in r2["groups"].values() for x in g}
        await hr.go(f"/desk/ai-ranking?opening={OP2}", 6)
        await hr.tall_shot("A5_ranking_jeddah")
        no_reason = await xcall(hr, "ido_talent_ai.api.decide", {"applicant": "applicant.2001@example.com", "status": "Rejected", "reason": " "})
        decided = await xcall(hr, "ido_talent_ai.api.decide", {"applicant": "applicant.2001@example.com", "status": "Shortlisted", "reason": "خبرة إشراف 7 سنوات ورخصة سارية — مناسب للمقابلة"})
        await hr.go("/desk/job-applicant/applicant.2001@example.com", 6)
        await hr.tall_shot("A5_decision_ai", selector=".frappe-control[data-fieldname=ai_html]")
        statuses = await xcall(hr, "frappe.client.get_list", {"doctype": "Job Applicant", "fields": ["name", "status", "ai_decided_by"], "limit_page_length": 500})
        changed = [x for x in statuses if x["status"] != "Open"]
        audits = await xcall(hr, "frappe.client.get_list", {"doctype": "AI Recruitment Audit Log", "filters": {"action": "hr.decision"}, "fields": ["reference_name", "actor", "reason"], "limit_page_length": 500})
        all_by_hr = all(x.get("ai_decided_by") for x in changed) and len(changed) == len({x["reference_name"] for x in audits})
        record("A5_openings_separate_and_status_only_by_hr", not (names1 & names2) and {"jeddah.1@example.com", "jeddah.2@example.com"} <= names2
               and isinstance(no_reason, dict) and "__error__" in no_reason and decided == {"status": "Shortlisted"} and all_by_hr,
               opening1=len(names1), opening2=sorted(n for n in names2 if n), overlap=sorted(names1 & names2),
               reason_required=bool(isinstance(no_reason, dict) and no_reason.get("__error__")), status_changes=len(changed),
               hr_decision_audits=len(audits))

        # Guide 1+: weights total enforced, impact preview, new version v2, results become stale
        prof = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"}))["ai_profile"]
        await hr.go(f"/desk/ai-job-profile/{prof}", 6)
        await hr.ev("""(async () => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'shifts').weight = 20; cur_frm.dirty(); await cur_frm.save(); })()""")
        await asyncio.sleep(3)
        blocked = await xcall(hr, "ido_talent_ai.profile.approve", {"name": prof})
        await hr.go(f"/desk/ai-job-profile/{prof}", 6)
        await hr.tall_shot("G1_weights_105")
        await hr.ev("""(async () => { const c = cur_frm.doc.criteria; c.find(x => x.criterion_key === 'licence').weight = 10; cur_frm.dirty(); await cur_frm.save(); })()""")
        await asyncio.sleep(3)
        await hr.go(f"/desk/ai-job-profile/{prof}", 6)
        await hr.ev("talent_ai_profile.impact(cur_frm, false)")
        await hr.wait_for("!!document.querySelector('.modal.show .tai table')", 60)
        await asyncio.sleep(2)
        await hr.tall_shot("G1_impact_preview", selector=".modal.show .modal-content")
        impact = await xcall(hr, "ido_talent_ai.profile.impact_preview", {"name": prof})
        await hr.ev("cur_dialog && cur_dialog.hide()")
        approved = await xcall(hr, "ido_talent_ai.profile.approve", {"name": prof})
        rk3 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        await hr.go(f"/desk/ai-ranking?opening={OP1}", 6)
        await hr.tall_shot("G1_ranking_stale_after_v2")
        record("G1_weights_impact_and_versions", isinstance(blocked, dict) and "__error__" in blocked and approved.get("version") == 2 and approved.get("stale", 0) > 0
               and len(rk3["groups"]["stale"]) > 0 and impact["summary"]["applicants"] > 0,
               approval_blocked_at_105=bool(blocked.get("__error__")) if isinstance(blocked, dict) else False, new_version=approved.get("version"),
               stale_after_approval=approved.get("stale"), impact_summary=impact["summary"], stale_group=len(rk3["groups"]["stale"]))
        res = await xcall(hr, "ido_talent_ai.api.rescreen_all", {"job_opening": OP1})
        await hr.go(f"/desk/ai-batch?opening={OP1}", 5)
        await asyncio.sleep(8)
        await hr.tall_shot("G7_batch_rescoring")
        t0 = time.time()
        while time.time() - t0 < 900:
            st = await xcall(hr, "ido_talent_ai.api.batch_status", {"job_opening": OP1})
            if not st["applicants"].get("Processing"):
                break
            await asyncio.sleep(10)
        rk4 = await xcall(hr, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        record("G7_rescore_all_after_v2", len(rk4["groups"]["stale"]) == 0 and rk4["job_version"] == 2, queued=res.get("queued"),
               seconds=round(time.time() - t0), ranked=rk4["ranked_total"], stale_left=len(rk4["groups"]["stale"]))

        # Guide 10+ / 10c: CSV for Excel and comparison
        csv = await hr.ev(f"fetch('/api/method/ido_talent_ai.api.export_ranking_csv?job_opening={OP1}').then(r => r.arrayBuffer()).then(b => Array.from(new Uint8Array(b).slice(0, 3)).join(',') + '|' + new TextDecoder().decode(b).split('\\n')[0])")
        record("G10_csv_utf8_bom_arabic", csv.startswith("239,187,191|") and "الترتيب" in csv, head=csv[:80])
        top = [x["applicant"] for x in rk4["ranked"][:3]]
        await hr.go(f"/desk/ai-ranking?opening={OP1}", 6)
        await hr.ev(f"talent_ai.openCompare({json.dumps(top)})")
        await hr.wait_for("!!document.querySelector('.modal.show .tai table.cmptable')", 60)
        await asyncio.sleep(2)
        await hr.tall_shot("G10c_compare", selector=".modal.show .modal-content")
        cmp_ = await xcall(hr, "ido_talent_ai.api.compare", {"applicants": json.dumps(top)})
        mixed = await xcall(hr, "ido_talent_ai.api.compare", {"applicants": json.dumps([top[0], "jeddah.1@example.com"])})
        record("G10c_compare_same_opening", len(cmp_["applicants"]) == 3 and isinstance(mixed, dict) and "__error__" in mixed,
               compared=[x["applicant_name"] for x in cmp_["applicants"]], refuses_mixed_openings=bool(mixed.get("__error__")))
        await hr.ev("cur_dialog && cur_dialog.hide()")

        # Guide 13: settings live in the engine
        before = eng("/v1/settings")["max_retries"]
        await xcall(hr, "frappe.client.set_value", {"doctype": "AI Recruitment Settings", "name": "AI Recruitment Settings", "fieldname": "max_retries", "value": before + 1})
        after = eng("/v1/settings")["max_retries"]
        await xcall(hr, "frappe.client.set_value", {"doctype": "AI Recruitment Settings", "name": "AI Recruitment Settings", "fieldname": "max_retries", "value": before})
        await hr.go("/desk/ai-recruitment-settings", 6)
        await hr.tall_shot("G13_settings")
        record("G13_settings_written_to_engine", after == before + 1 and eng("/v1/settings")["max_retries"] == before, before=before, after_change=after)

        # A6: engine down -> the application is still saved; Failed after retries; retry later works
        compose("stop", "api")
        try:
            async with Browser(BASE, OUT, port=18096, height=1400) as guest:
                ok6, secs6 = await submit_form(guest, OP1, applicant("2017", applicant_name="منصور العتيبي", email_id="a6.down@example.com", national_id="1000099006"), "A6_form_engine_down")
            failed = await wait_value(hr, "Job Applicant", "a6.down@example.com", "ai_status", lambda v: v == "Failed", 400)
            job = await xcall(hr, "frappe.client.get_list", {"doctype": "AI Recruitment Job", "filters": {"reference_name": "a6.down@example.com"}, "fields": ["name", "status", "attempts", "error_message"]})
            await hr.go("/desk/job-applicant/a6.down@example.com", 6)
            await hr.tall_shot("A6_failed_ai", selector=".frappe-control[data-fieldname=ai_html]")
        finally:
            compose("start", "api")
        for _ in range(60):
            try:
                if eng("/v1/settings"):
                    break
            except Exception:
                await asyncio.sleep(2)
        await hr.go("/desk/job-applicant/a6.down@example.com", 6)
        await hr.ev("document.querySelector('[data-tai=retry]').click()")
        recovered = await wait_value(hr, "Job Applicant", "a6.down@example.com", "ai_status", lambda v: v in ("Completed", "Needs Review"), 300)
        await hr.go("/desk/job-applicant/a6.down@example.com", 6)
        await hr.tall_shot("A6_after_retry_ai", selector=".frappe-control[data-fieldname=ai_html]")
        record("A6_application_works_when_engine_is_down", ok6 and failed == "Failed" and recovered in ("Completed", "Needs Review"),
               saved_in_s=secs6, status_while_down=failed, job=job[0] if job else None, after_retry=recovered)

        await hr.go(f"/desk/ai-recruitment-audit-log", 5)
        await hr.tall_shot("G14_audit_log")

    await roles()


async def call_status(b, method, args):
    """POST a whitelisted method with fetch (the website helper never settles on a 403)."""
    return await b.ev(f"""fetch('/api/method/{method}', {{method: 'POST', headers: {{'Content-Type': 'application/json', 'Accept': 'application/json',
        'X-Frappe-CSRF-Token': (window.frappe && frappe.csrf_token) || ''}}, body: JSON.stringify({json.dumps(args, ensure_ascii=False)})}})
        .then(async r => ({{status: r.status, body: (await r.text()).slice(0, 160)}}))""")


async def roles():
    async with Browser(BASE, OUT, port=18097, height=1100) as emp:
        await emp.login("employee@example.com", DEV["EMPLOYEE_PASSWORD"])
        await emp.go("/desk", 5)
        r = await call_status(emp, "ido_talent_ai.api.ranking", {"job_opening": OP1})
        d = await call_status(emp, "ido_talent_ai.api.decide", {"applicant": "applicant.2002@example.com", "status": "Rejected", "reason": "x"})
        g = await call_status(emp, "frappe.client.get", {"doctype": "Job Applicant", "name": "applicant.2002@example.com"})
        await emp.go("/desk/job-applicant/applicant.2002@example.com", 6)
        await emp.tall_shot("A8_employee_denied")
        record("A8_employee_cannot_see_or_decide", all(x and x["status"] in (401, 403) for x in (r, d, g)),
               ranking=r and r["status"], decide=d and d["status"], read_applicant=g and g["status"])
    async with Browser(BASE, OUT, port=18098, height=1100) as hru:
        await hru.login("hr.user@example.com", DEV["HR_USER_PASSWORD"])
        await hru.go("/desk/job-applicant/applicant.2002@example.com", 7)
        await hru.wait_for("!!document.querySelector('.frappe-control[data-fieldname=ai_html] .tai .card')", 40)
        has = await hru.ev("!!document.querySelector('.frappe-control[data-fieldname=ai_html] .tai .card')")
        rtl = await hru.ev("document.documentElement.dir")
        await hru.tall_shot("A8_hr_user_ai", selector=".frappe-control[data-fieldname=ai_html]")
        record("A8_hr_user_sees_ai_section_in_arabic_rtl", has and rtl == "rtl", ai_section=has, dir=rtl, js_errors=len(hru.errors))

def finalize():
    REPORT["passed"] = sum(1 for c in REPORT["checks"].values() if c["ok"])
    REPORT["total"] = len(REPORT["checks"])
    with open(os.path.join(OUT, "acceptance.json"), "w", encoding="utf-8") as f:
        json.dump(REPORT, f, ensure_ascii=False, indent=1)
    print(f"\n{REPORT['passed']}/{REPORT['total']} checks passed; screenshots and acceptance.json in {OUT}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "--roles-only":
        prev = os.path.join(OUT, "acceptance.json")
        if os.path.exists(prev):
            REPORT["checks"].update(json.load(open(prev, encoding="utf-8")).get("checks", {}))
        asyncio.run(roles())
    else:
        asyncio.run(main())
    finalize()
