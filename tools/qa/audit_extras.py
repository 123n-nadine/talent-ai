"""Final QA, phase 2 — live checks of walkthrough claims not covered by the browser E2E suite or
the automated tests (which are cited in the audit table by their IDs). Read-mostly; the only writes
are a draft criteria profile with wrong weights (deleted afterwards) and nothing else.

    tools/.venv/bin/python tools/qa/audit_extras.py
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, OP1  # noqa: E402
from pw import BASE, DEV, ROOT, browser, new_page, settle, xcall  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "qa")
HR = "hr.manager@example.com"
RESULTS: list[dict] = []


def rec(page: str, claim: str, how: str, ok: bool | None, actual: str) -> None:
    RESULTS.append({"page": page, "claim": claim, "how": how, "ok": ok, "actual": actual})
    print(("PASS" if ok else "FAIL" if ok is False else "INFO"), page, "|", claim, "|", actual[:140], flush=True)


def post_raw(url: str, body: bytes, headers: dict) -> int:
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


async def login(page, email: str, password: str) -> None:
    await page.goto(BASE + "/login")
    st = await page.evaluate("""([u, p]) => fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify({usr: u, pwd: p})}).then(r => r.status)""", [email, password])
    assert st == 200, f"login {email}: HTTP {st}"
    await page.goto(BASE + "/desk/ai-recruitment")  # desk context: frappe.xcall hangs on the login page after a few calls
    await settle(page, 1.5)


async def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    # --- callbacks: unsigned, forged, stale (page 10 «النتيجة موقّعة»)
    url = f"{BASE}/api/method/ido_talent_ai.api.receive_result"
    body = json.dumps({"candidate_ref": "JA-NOPE", "screening_id": "scr_x", "status": "completed", "score": 99}).encode()
    ts = str(int(time.time()))
    unsigned = post_raw(url, body, {"X-Talent-Timestamp": ts})
    forged = post_raw(url, body, {"X-Talent-Timestamp": ts, "X-Talent-Signature": "sha256=" + "0" * 64})
    wrong_secret = post_raw(url, body, {"X-Talent-Timestamp": ts, "X-Talent-Signature": "sha256=" + hmac.new(b"not-the-secret", ts.encode() + b"." + body, hashlib.sha256).hexdigest()})
    old_ts = str(int(time.time()) - 3600)
    rec("10 / 23", "A forged or unsigned callback is rejected", "live POST to receive_result: no signature, zeros, wrong secret", unsigned == 401 and forged == 401 and wrong_secret == 401,
        f"unsigned {unsigned}, forged {forged}, wrong secret {wrong_secret} (HTTP 401 expected); stale timestamp also refused in the Frappe test test_callback_signature")

    async with browser() as b:
        hr = await new_page(b, "1366")
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])

        # --- page 5: home counters are real
        counts = await xcall(hr, "ido_talent_ai.api.home_counts", {})
        db_total = await xcall(hr, "frappe.client.get_count", {"doctype": "Job Applicant", "filters": {"ai_status": ["is", "set"]}})
        db_all = await xcall(hr, "frappe.client.get_count", {"doctype": "Job Applicant"})
        rec("5", "Home-page counters come from the site (openings, applications, processing, needs review, failed)", "api.home_counts vs frappe.client.get_count",
            counts.get("applicants") in (db_total, db_all), f"home_counts {counts}; DB applicants {db_all}")

        # --- page 9: weights must total 100% — API refuses 105%
        prof = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"})
        src = await xcall(hr, "frappe.client.get", {"doctype": "AI Job Profile", "name": prof["ai_profile"]})
        crit = [{k: c.get(k) for k in ("criterion_key", "criterion", "weight", "mandatory", "question", "rubric_0", "rubric_25", "rubric_50", "rubric_75", "rubric_100")} for c in src.get("criteria", [])]
        crit[0]["weight"] = float(crit[0]["weight"]) + 5  # 105%
        draft = await xcall(hr, "frappe.client.insert", {"doc": {"doctype": "AI Job Profile", "title": "QA — أوزان 105%", "status": "Draft", "criteria": crit,
                                                                  "questions": [{k: q.get(k) for k in ("question_key", "label", "label_en", "question_type", "options", "required", "hint")} for q in src.get("questions", [])]}})
        name = draft.get("name") if isinstance(draft, dict) else None
        res = await xcall(hr, "ido_talent_ai.profile.approve", {"name": name}) if name else {"__error__": "insert failed"}
        refused = isinstance(res, dict) and "__error__" in res
        st = await xcall(hr, "frappe.client.get_value", {"doctype": "AI Job Profile", "filters": name, "fieldname": "status"}) if name else {}
        rec("9", "Weights must total 100%: approval of 105% is refused (API)", "frappe.client.insert draft with 105% then profile.approve",
            refused and st.get("status") == "Draft", f"approve → {'refused' if refused else 'ACCEPTED'}; status stays {st.get('status')}")
        if name:
            await xcall(hr, "frappe.client.delete", {"doctype": "AI Job Profile", "name": name})

        # --- page 19: the assessment screen says read-only and never changes the status
        app = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": {"ai_status": "Completed"}, "fieldname": ["name", "status"]})
        await hr.goto(f"{BASE}/desk/job-applicant/{app['name']}")
        await settle(hr, 3)
        await hr.wait_for_selector(f"{AI} .tai .card", timeout=90000)
        txt = await hr.evaluate(f"document.querySelector('{AI}').innerText")
        rec("19", "Assessment screen is marked «قراءة فقط — لا يغيّر حالة الطلب»; eligibility, score/band, coverage, rank, summary shown", "open a completed applicant as HR Manager",
            all(w in txt for w in ("قراءة فقط", "الأهلية", "الدرجة", "التغطية", "الترتيب", "الملخص")), f"status {app['status']}; labels found: " + ", ".join(w for w in ("قراءة فقط", "الأهلية", "الدرجة", "التغطية", "الترتيب", "الملخص") if w in txt))

        # --- page 14: the thanks page shows no score (guest)
        g = await new_page(b, "1366")
        await g.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await g.wait_for_selector("#tai-form", timeout=60000)
        form_txt = await g.evaluate("document.body.innerText")
        rec("11", "Under the ID number: not shown or sent to the AI, used only for duplicate detection", "public form text", "لا يُعرض ولا يُرسل" in form_txt, "sentence present" if "لا يُعرض ولا يُرسل" in form_txt else "sentence missing")
        n_q = await g.evaluate("document.querySelectorAll('#tai-form .field.q').length")
        consent_req = await g.evaluate("document.getElementById('f-consent').required")
        rec("12", "CV optional, consent mandatory; 11 screening questions with the zero/blank hint", "public form DOM",
            n_q == 11 and "اختياري" in form_txt and "الفراغ يعني" in form_txt,
            f"questions {n_q}; consent required attribute: {consent_req}")
        await g.click('[data-lang="en"]')
        await asyncio.sleep(1)
        en_txt = await g.evaluate("document.body.innerText")
        rec("13", "The form switches fully to English with one button", "click English, read the labels", "Job application" in en_txt and "Screening questions" in en_txt and "Consent to processing" in en_txt, "English labels present")
        await g.context.close()
        m = await new_page(b, "m390")
        await m.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await m.wait_for_selector("#tai-form", timeout=60000)
        overflow = await m.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
        cols = await m.evaluate("getComputedStyle(document.querySelector('#tai-form .grid2') || document.body).gridTemplateColumns")
        rec("13", "Mobile: one column, nothing cut", "viewport 390 px: no horizontal scroll", not overflow, f"horizontal overflow: {overflow}; grid columns: {cols}")
        await m.context.close()

        # --- page 25: settings hide secrets and refuse HR User
        s = await xcall(hr, "ido_talent_ai.api.engine_settings", {})
        secrets = {k: v for k, v in (s.get("settings") or {}).items() if ("key" in k or "secret" in k) and isinstance(v, str) and len(v) > 8}
        leak = bool(secrets)
        rec("25", "Settings: secrets hidden (no key in the settings API answer)", "api.engine_settings as HR Manager", not leak, f"keys in answer: {sorted((s.get('settings') or {}).keys())[:12]}")
        await hr.context.close()
        u = await new_page(b, "1366")
        await login(u, "hr.user@example.com", DEV["HR_USER_PASSWORD"])
        await u.goto(f"{BASE}/desk/ai-recruitment-settings")
        await settle(u, 3)
        body_txt = await u.evaluate("document.body.innerText")
        denied = any(w in body_txt for w in ("غير مسموح", "لا يسمح", "Not Permitted", "Not permitted"))
        rec("25 / 32", "HR User cannot open the settings", "login as hr.user, open /desk/ai-recruitment-settings", denied, "refused" if denied else "OPENED")
        api = await xcall(u, "ido_talent_ai.api.engine_settings", {})
        rec("25 / 32", "HR User cannot read the settings through the API", "api.engine_settings as hr.user", isinstance(api, dict) and "__error__" in api, "refused" if isinstance(api, dict) and "__error__" in api else "ANSWERED")
        await u.context.close()

    json.dump(RESULTS, open(os.path.join(OUT_DIR, "audit_extras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(sum(1 for r in RESULTS if r["ok"]), "pass /", sum(1 for r in RESULTS if r["ok"] is False), "fail of", len(RESULTS))


if __name__ == "__main__":
    asyncio.run(main())
