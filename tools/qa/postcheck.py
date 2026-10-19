"""Final QA — follow-up of the exploratory cases that needed a second look (run after the fixes,
on a running stack; creates a few synthetic applicants, so reset the demo afterwards):

  1. 0-byte CV: refused at submission with a clear message (Q6), nothing saved
  2. 3-page PDF: all pages read (page count and characters from the engine's document record)
  3. HTML/script in the name and a free answer: what is stored and what the HR page shows
  4. public-form rate limit: the site setting is cached per web process — clear the cache after
     changing it, then the sixth submission is refused with 429
  5. Redis restart mid-screening: the workers come back (restart policy), the application's fate

    tools/.venv/bin/python tools/qa/postcheck.py
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore import HR, RESULTS, apply_http, bench, compose, final, make_files, rec  # noqa: E402
from full_test import CVS, OP1, applicant, open_applicant, submit_public  # noqa: E402
from pw import BASE, DEV, ROOT, browser, new_page, settle, wait_value, xcall  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "qa")


def workers_up() -> int:
    out = subprocess.run(["docker", "ps", "--filter", "name=talentai-worker", "--format", "{{.Names}} {{.Status}}"], capture_output=True, text=True).stdout
    return sum(1 for ln in out.splitlines() if " Up " in ln)


async def main() -> None:
    f = make_files()
    only = os.environ.get("QA_ONLY", "123456")
    async with browser() as b:
        hr = await new_page(b, "1366")
        await hr.goto(BASE + "/login")
        st = await hr.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [HR, DEV["HR_MANAGER_PASSWORD"]])
        assert st == 200
        await hr.goto(BASE + "/desk/ai-recruitment")
        await settle(hr, 1.5)
        g = await new_page(b, "1366")

        # 1 — 0-byte file
        if "1" in only:
            a = applicant("2002", applicant_name="اختبار ملف فارغ", email_id="q3.empty@example.com", national_id="1000009801")
            sub = await submit_public(g, OP1, a, f["empty"])
            sc, body = apply_http(None, "q3.empty.http@example.com", "1000009802", "اختبار ملف فارغ", f["empty"])
            n = await xcall(hr, "frappe.client.get_count", {"doctype": "Job Applicant", "filters": {"email_id": ["in", ["q3.empty@example.com", "q3.empty.http@example.com"]]}})
            rec("files", "0-byte file (after Q6)", "refused in the form and by the endpoint with «ملف السيرة فارغ»; nothing saved",
                f"form: {'refused' if not sub.get('ok') else 'ACCEPTED'} {sub.get('errors')}; endpoint HTTP {sc} {'فارغ' in body}; saved {n}",
                (not sub.get("ok")) and sc == 422 and "فارغ" in body and n == 0)

        # 2 — multi-page PDF
        if "2" in only:
            a = applicant("2002", applicant_name="اختبار ثلاث صفحات", email_id="q4.multi@example.com", national_id="1000009808")
            sub = await submit_public(g, OP1, a, f["multi"])
            assert sub.get("ok"), sub
            st, secs, info = await final(hr, "q4.multi@example.com")
            d = await xcall(hr, "ido_talent_ai.api.cv_analysis", {"applicant": info["name"]})
            pages, chars, meth = d.get("pages"), d.get("chars"), d.get("extraction_method")
            rec("files", "multi-page PDF (3 pages)", "all pages read", f"ai_status {st} after {secs}s; method {meth}; pages {pages}; chars {chars}; flags {info['flags']}",
                st in ("Completed", "Needs Review") and (pages or 0) >= 3)

        # 3 — HTML/script
        if "3" in only:
            a = applicant("2003", applicant_name="<img src=x onerror=alert(1)>عمر", email_id="q3.html@example.com", national_id="1000009804")
            a["answers"] = {**a["answers"], "last_job": "<script>alert('x')</script><b>مشرف</b> وردية منذ 2019"}
            sub = await submit_public(g, OP1, a, None)
            assert sub.get("ok"), sub
            st, secs, info = await final(hr, "q3.html@example.com")
            doc = await xcall(hr, "frappe.client.get", {"doctype": "Job Applicant", "name": info["name"]})
            stored_name = doc.get("applicant_name")
            stored_answer = next((r.get("answer") for r in doc.get("ai_answers", []) if r.get("question_key") == "last_job"), None)
            await hr.evaluate("window.__alerts = 0; window.alert = () => { window.__alerts++; }")
            await open_applicant(hr, info["name"], wait_card=False)
            await asyncio.sleep(2)
            injected = await hr.evaluate("!!document.querySelector('img[src=\"x\"]') || document.title.includes('alert')")
            alerts = await hr.evaluate("window.__alerts || 0")
            rec("text", "HTML/script in the name and a free answer", "no script runs; stored and shown as harmless text",
                f"stored name {stored_name!r}; stored answer {stored_answer!r}; injected element {injected}; alerts {alerts}; ai_status {st}",
                not injected and alerts == 0 and "<script" not in (stored_answer or "") and "onerror" not in (stored_name or ""))

        # 4 — rate limit with the cache cleared after the setting
        if "4" in only:
            try:
                # Frappe keeps site_config.json in memory for 60 s per web process: wait it out after each change.
                # The 10-minute window also counts this IP's earlier submissions, so the probe expects at most
                # five accepted, then only refusals, and a normal submission again once the limit is restored.
                bench("bench --site talent.localhost set-config talent_ai_apply_limit 5 >/dev/null")
                time.sleep(65)
                codes = [apply_http(None, f"q4.rate{i}@example.com", f"10000097{10 + i:02d}", "اختبار حد التقديم")[0] for i in range(8)]
                n_ok = codes.count(200)
                monotonic = codes == [200] * n_ok + [429] * (len(codes) - n_ok)
            finally:
                bench("bench --site talent.localhost set-config talent_ai_apply_limit 100 >/dev/null")
                time.sleep(65)
            after = apply_http(None, "q4.rate.after@example.com", "1000009730", "اختبار حد التقديم")[0]
            rec("security", "public-form rate limit (5 per 10 min for the probe)", "at most 5 accepted in the window, then 429 only; normal again after the limit is restored",
                f"codes {codes}; after restoring 100: HTTP {after}", n_ok <= 5 and monotonic and 429 in codes and after == 200)

        # 5 — Redis restart mid-screening with the restart policy in place
        if "5" in only:
            email = "q4.restart.redis@example.com"
            a = applicant("2002", applicant_name="اختبار إعادة تشغيل Redis", email_id=email, national_id="1000009807")
            sub = await submit_public(g, OP1, a, os.path.join(CVS, "demo-majed-cv.jpg"))
            if not sub.get("ok") and "الحد" in str(sub.get("errors")):  # the limit of the probe still cached: wait and retry once
                await asyncio.sleep(15)
                sub = await submit_public(g, OP1, a, os.path.join(CVS, "demo-majed-cv.jpg"))
            assert sub.get("ok"), sub
            await asyncio.sleep(6)
            before = workers_up()
            t0 = time.time()
            compose("restart", "redis")
            restart_s = round(time.time() - t0, 1)
            back = None
            for _ in range(60):
                if workers_up() == before:
                    back = round(time.time() - t0, 1)
                    break
                time.sleep(2)
            st, secs, info = await final(hr, email, timeout=300)
            rec("behaviour", "restart engine Redis mid-processing (with restart: on-failure)", "workers back by themselves; the application not lost",
                f"restart took {restart_s}s; workers before {before}, back after {back}s ({workers_up()} up); ai_status after 5 min: {st} ({secs}s); flags {info['flags']}",
                back is not None and workers_up() == before)
        # 6 — the engine's Redis is down when an application arrives (Q7b): failed with a reason, retry works
        if "6" in only:
            email = "q4.redis.down@example.com"
            compose("stop", "redis")
            try:
                a = applicant("2003", applicant_name="اختبار توقف Redis", email_id=email, national_id="1000009806")
                sub = await submit_public(g, OP1, a, None)
                assert sub.get("ok"), sub
                name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": email, "fieldname": "name"}))["name"]
                st1, t1 = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v == "Failed", 300, 3.0)
                res = await xcall(hr, "ido_talent_ai.api.get_assessment", {"applicant": name})
                job = (res.get("jobs") or [{}])[0]
            finally:
                compose("start", "redis")
            back = None
            t0 = time.time()
            for _ in range(90):
                if workers_up() == 4:
                    back = round(time.time() - t0, 1)
                    break
                time.sleep(2)
            r = await xcall(hr, "ido_talent_ai.api.retry_job", {"job": job.get("name")})
            st2, t2 = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 300, 2.0)
            st2, t2 = (st2, t2) if st2 != "Processing" else (st2, t2)
            ref = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": name, "fieldname": "ai_candidate_ref"})).get("ai_candidate_ref")
            q = ("from sqlalchemy import text\nfrom app.core.config import get_settings\nfrom app.storage.db import make_engine\n"
                 "e = make_engine(get_settings().database_url)\nwith e.connect() as c:\n"
                 f"    print([r[0] for r in c.execute(text(\"select s.status from screenings s join candidates c on c.id=s.candidate_id where c.external_ref=:r order by s.created_at\"), {{'r': '{ref}'}})])\n")
            states = subprocess.run(["docker", "exec", "-i", "talentai-api-1", "python", "-"], input=q, capture_output=True, text=True).stdout.strip()
            rec("behaviour", "engine Redis down when an application arrives (after Q7b)", "Failed with a reason (never stuck); workers back; HR retry → assessed; no screening left «queued»",
                f"Failed after {t1}s ({job.get('attempts')}/{job.get('max_attempts')} attempts: {job.get('error_message')}); workers back {back}s after the start; retry {'ok' if not (isinstance(r, dict) and '__error__' in r) else r} → {st2} in {t2}s; engine screenings {states}",
                st1 == "Failed" and back is not None and st2 in ("Completed", "Needs Review") and "queued" not in states)

        await g.context.close()
        await hr.context.close()
    # keep the results of parts not rerun this time (QA_ONLY), replace the ones that were
    path = os.path.join(OUT_DIR, "postcheck.json")
    old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    new_keys = {r["case"].split(" (")[0] for r in RESULTS}
    merged = [r for r in old if r["case"].split(" (")[0] not in new_keys] + RESULTS
    json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["| area | case | expected | actual | result |", "|---|---|---|---|---|"]
    for r in merged:
        md.append(f"| {r['area']} | {r['case']} | {r['expected']} | {r['actual'].replace('|', '/')} | {'PASS' if r['ok'] else 'FAIL' if r['ok'] is False else 'INFO'} |")
    open(os.path.join(OUT_DIR, "postcheck.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(sum(1 for r in RESULTS if r["ok"]), "pass /", sum(1 for r in RESULTS if r["ok"] is False), "fail of", len(RESULTS))


if __name__ == "__main__":
    asyncio.run(main())
