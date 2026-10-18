"""Demo rehearsal: the fifteen screens of the presentation, in the order Nadine shows them, taken
by a real browser on the clean demo (run dev-frappe/reset_demo.sh first and again afterwards).

Writes demo/screens/NN_name.png and demo/STEPS.md (link, user, what to click, what appears, how
long the step took). The one write it makes to the demo is the application of a new applicant with
a scanned CV and one HR decision — exactly what the presentation does; the reset undoes both.

    tools/.venv/bin/python tools/demo/rehearsal.py
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from full_test import AI, CVS, OP1, applicant, open_applicant, submit_public  # noqa: E402
from pw import BASE, DEV, ROOT, browser, compact_png, new_page, settle, shot, wait_value, xcall  # noqa: E402

OUT = os.path.join(ROOT, "demo", "screens")
STEPS_MD = os.path.join(ROOT, "demo", "STEPS.md")
TS = os.environ.get("TAILSCALE_IP") or DEV.get("TAILSCALE_IP") or "100.85.37.127"
LAPTOP = f"http://{TS}:18050"  # what the presenter types from the laptop
HR = "hr.manager@example.com"
HRU = "hr.user@example.com"
NEW = {"name": "ماجد الشهراني", "email": "demo.majed@example.com", "nid": "1000009901"}
STEPS: list[dict] = []
T0 = time.time()


def step(n: int, title: str, url: str, user: str, click: str, result: str, png: str, t: float) -> None:
    STEPS.append({"n": n, "title": title, "url": url, "user": user, "click": click, "result": result, "png": png, "s": round(t, 1)})
    print(f"{n:02d} {title} ({t:.1f}s)", flush=True)


async def snap(page, name: str, selector: str | None = None, pad: int = 0) -> str:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    await shot(page, path, selector=selector, pad=pad)
    compact_png(path)
    return f"screens/{name}.png"


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


async def go(page, url: str, wait: str | None = None, extra: float = 2.0) -> None:
    await page.goto(BASE + url)
    await settle(page, extra)
    if wait:
        await page.wait_for_function(wait, timeout=90000)
        await asyncio.sleep(1.0)


def card(title_re: str) -> str:
    return (f"Array.from(document.querySelectorAll('{AI} .tai .card')).find(c => /{title_re}/.test(c.querySelector('h2') ? c.querySelector('h2').innerText : ''))")


async def mark(page, js_find: str) -> str:
    await page.evaluate(f"""() => {{ document.querySelectorAll('[data-g]').forEach(e => e.removeAttribute('data-g'));
        const e = ({js_find}); if (e) e.setAttribute('data-g', '1'); return !!e; }}""")
    return "[data-g='1']"


def compose(*args: str) -> None:
    subprocess.run([os.path.join(ROOT, "talent-engine", "scripts", "compose.sh"), *args], check=True, capture_output=True)


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    async with browser() as b:
        hr = await new_page(b, "1366", scale=1.5)
        await login(hr, HR, DEV["HR_MANAGER_PASSWORD"])

        # 1 home
        t = time.time()
        await go(hr, "/desk/ai-recruitment", "!!document.querySelector('.tai-home-grid')")
        png = await snap(hr, "01_home", await visible(hr))
        step(1, "الصفحة الرئيسية «التوظيف الذكي»", f"{LAPTOP}/desk/ai-recruitment", HR, "تسجيل الدخول بيفتحها لوحده؛ لو مش ظاهرة اضغطي «التوظيف الذكي» في القائمة الجانبية",
             "العدّادات الخمسة فوق (شواغر، طلبات، جاري المعالجة، يحتاج مراجعة، فشل) وتحتها تسع أزرار الدورة بالترتيب", png, time.time() - t)

        # 2 criteria profile
        t = time.time()
        prof = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Opening", "filters": OP1, "fieldname": "ai_profile"}))["ai_profile"]
        await go(hr, f"/desk/ai-job-profile/{prof}", "window.cur_frm && cur_frm.doc && cur_frm.doc.name")
        png = await snap(hr, "02_profile", await visible(hr))
        step(2, "ملف المعايير «مشرف أمن — الرياض»", f"{LAPTOP}/desk/ai-job-profile/{prof}", HR, "الزرار الأول في الرئيسية «ملف المعايير» ثم الملف «مشرف أمن — الرياض»",
             "الشروط الإلزامية (الجنسية، الطول، الوزن، السن)، وجدول المعايير السبعة بأوزانها (مجموعها 100%)، وأسئلة الفرز، وحالة «معتمد»", png, time.time() - t)

        # 3 public job page
        t = time.time()
        g = await new_page(b, "1366", scale=1.5)
        await g.goto(BASE + "/jobs/security/security-supervisor-riyadh")
        await settle(g, 2)
        await g.wait_for_function("!!document.querySelector('.tai-reqs')", timeout=60000)
        png = await snap(g, "03_job_page", ".page_content, .page-content-wrapper, main")
        step(3, "صفحة الوظيفة العامة (زي ما المتقدم بيشوفها)", f"{LAPTOP}/jobs/security/security-supervisor-riyadh", "زائر (بدون دخول) — افتحيها في نافذة خاصة",
             "من الرئيسية الزرار الثالث «صفحة التقديم العامة» ثم الوظيفة «مشرف أمن — الرياض»", "وصف الوظيفة، ومربع «شروط التقديم» الأربعة، وزرار «قدّم الآن»", png, time.time() - t)

        # 4-5 apply as a new applicant with the scanned CV
        t = time.time()
        a = applicant("2002", applicant_name=NEW["name"], email_id=NEW["email"], national_id=NEW["nid"])
        sub = await submit_public(g, OP1, a, os.path.join(CVS, "HR-APP-2026-2002.jpg"), filled_shot=None, thanks_shot=None)
        assert sub.get("ok"), sub
        thanks_png = await snap(g, "05_thanks", ".formcard")
        t6 = time.time()
        name = (await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": NEW["email"], "fieldname": "name"}))["name"]
        # at once, without waiting for the network to go quiet: the page polls the engine every
        # second while the screening runs, so «idle» only comes when it is over
        await hr.goto(f"{BASE}/desk/job-applicant/{name}", wait_until="domcontentloaded")
        await asyncio.sleep(6)  # what the page shows a few seconds after the submission: status and the live stages
        processing_png = await snap(hr, "06_processing", await visible(hr))
        processing_state = await xcall(hr, "frappe.client.get_value", {"doctype": "Job Applicant", "filters": name, "fieldname": "ai_status"})
        processing_s = time.time() - t6
        # the filled form is shown after the real submission: re-open and fill it without sending
        await g.goto(f"{BASE}/ai-apply/new?job_title={OP1}")
        await g.wait_for_selector("#tai-form", timeout=60000)
        from full_test import FILL_JS, form_values

        vals, ans = form_values(a)
        await g.evaluate(FILL_JS, [vals, ans])
        await g.set_input_files("#f-cv", os.path.join(CVS, "HR-APP-2026-2002.jpg"))
        await g.evaluate("window.scrollTo(0, 0)")
        png = await snap(g, "04_apply_form", "#tai-form")
        step(4, "نموذج التقديم بسيرة ممسوحة (متقدم جديد)", f"{LAPTOP}/ai-apply/new?job_title={OP1}", "زائر",
             f"«قدّم الآن» ← املي البيانات (الاسم {NEW['name']}، الإيميل {NEW['email']}) والأسئلة ← «Choose File» واختاري الصورة الممسوحة ← علّمي «موافقة على المعالجة» ← «إرسال الطلب»",
             f"الطلب اتبعت في {sub.get('submit_s')} ثانية ورسالة الشكر ظهرت (الصورة الجاية)", png, time.time() - t)
        step(5, "رسالة الشكر بعد الإرسال", "نفس الصفحة بعد الإرسال", "زائر", "لا شيء — بتظهر لوحدها بعد «إرسال الطلب»",
             f"علامة صح، واسم الوظيفة، وجملة إن الموارد البشرية هي اللي هتراجع؛ مفيش أي درجة للمتقدم (الإرسال خد {sub.get('submit_s')} ثانية)", thanks_png, 0.0)
        await g.context.close()

        # 6 processing while it runs (captured right after the submission, above)
        st = processing_state.get("ai_status")
        step(6, "طلب المتقدم أثناء المعالجة", f"{LAPTOP}/desk/job-applicant/{name}", HR, "من الرئيسية «قائمة المتقدمين» ثم الطلب الجديد (أو افتحي الرابط فورًا بعد الإرسال)",
             f"الحالة «{ {'Processing': 'جاري المعالجة', 'Completed': 'مكتمل', 'Needs Review': 'يحتاج مراجعة'}.get(st, st)}» ورسالة «جاري المعالجة… تتحدث هذه الشاشة تلقائيًا عند وصول النتيجة» مكان التقييم؛ أول ما النتيجة توصل (حوالي 40 ثانية للسيرة الممسوحة) كارت التقييم ومراحل المعالجة العشرة بيظهروا لوحدهم من غير تحديث للصفحة", processing_png, processing_s)

        # 7 CV analysis (after the result)
        t = time.time()
        final, secs = await wait_value(hr, "Job Applicant", name, "ai_status", lambda v: v in ("Completed", "Needs Review", "Failed"), 600, 1.0)
        await open_applicant(hr, name)
        await hr.evaluate(f"talent_ai.openCvAnalysis({json.dumps(name)})")
        await hr.wait_for_selector(".modal.show .tai .pageview img", timeout=90000)
        await asyncio.sleep(2)
        png = await snap(hr, "07_cv_analysis", ".modal.show .modal-content")
        await hr.evaluate("cur_dialog && cur_dialog.hide()")
        step(7, "تحليل السيرة الممسوحة", f"{LAPTOP}/desk/job-applicant/{name}", HR, "زرار «تحليل السيرة» فوق الطلب (مجموعة Talent AI)",
             f"صورة السيرة وعليها مربعات القراءة بالألوان حسب الثقة، والنص المستخرج سطر سطر، وإخفاء الهوية قبل وبعد (النتيجة ظهرت بعد {secs} ثانية من الإرسال)", png, time.time() - t)

        # 8 assessment
        t = time.time()
        await open_applicant(hr, name)
        png = await snap(hr, "08_assessment", await mark(hr, f"document.querySelector('{AI}')"))
        step(8, "شاشة التقييم", f"{LAPTOP}/desk/job-applicant/{name}", HR, "انزلي لقسم «تقييم الذكاء الاصطناعي» في نفس الطلب",
             "الدرجة والفئة والأهلية، ونقاط القوة والنواقص، وجدول المعايير معيار معيار مع الدليل (إجابة النموذج والجملة من السيرة)، ونص السيرة كما يراه النموذج", png, time.time() - t)

        # 9-10 ranking and compare
        t = time.time()
        await go(hr, f"/desk/ai-ranking?opening={OP1}", "!!document.querySelector('.tai .rankrow')", 3)
        png = await snap(hr, "09_ranking", await visible(hr))
        step(9, "الترتيب", f"{LAPTOP}/desk/ai-ranking?opening={OP1}", HR, "من الرئيسية الزرار الخامس «الترتيب» واختاري «مشرف أمن — الرياض»",
             "المستوفين مرتبين من الأعلى للأقل بالدرجة والفئة ونقاط القوة، وتحتهم المجموعات المقفولة (غير مستوفين، يحتاج مراجعة، مكرر، بانتظار الموافقة…)", png, time.time() - t)
        t = time.time()
        await hr.wait_for_selector(".tai .rankrow [data-sel]", timeout=60000)
        boxes = hr.locator(".tai .rankrow [data-sel]")
        for i in range(3):
            await boxes.nth(i).check()
        await hr.evaluate("""() => { const b = Array.from(document.querySelectorAll('.page-actions button, .page-actions .btn')).find(x => /مقارنة|Compare/.test(x.innerText)); b.click(); }""")
        await hr.wait_for_selector(".modal.show .tai table.cmptable", timeout=60000)
        await asyncio.sleep(2)
        png = await snap(hr, "10_compare", ".modal.show .modal-content")
        await hr.evaluate("cur_dialog && cur_dialog.hide()")
        step(10, "مقارنة ثلاثة متقدمين", f"{LAPTOP}/desk/ai-ranking?opening={OP1}", HR, "علّمي المربع جنب أول ثلاثة في الترتيب ثم زرار «مقارنة» فوق",
             "جدول جنب بعض: كل معيار في سطر، ولكل متقدم مستواه ودليله، والدرجة في الآخر", png, time.time() - t)

        # 11-12 decision with a reason
        t = time.time()
        await open_applicant(hr, name)
        await hr.evaluate("talent_ai_form.decide(cur_frm, 'Shortlisted')")
        await hr.wait_for_selector(".modal.show [data-fieldname=reason] textarea", timeout=20000)
        await asyncio.sleep(0.8)  # the dialog object is set once it is shown
        reason = "خبرة إشراف أربع سنوات ورخصة سارية، والسيرة تؤكد الإجابات — مناسب للمقابلة"
        await hr.evaluate(f"cur_dialog.set_value('reason', {json.dumps(reason)})")
        await asyncio.sleep(0.4)
        png = await snap(hr, "11_decision_dialog", ".modal.show .modal-content")
        await hr.evaluate("cur_dialog.get_primary_btn().click()")
        await asyncio.sleep(3)
        step(11, "قرار الموارد البشرية بسبب", f"{LAPTOP}/desk/job-applicant/{name}", HR, "زرار «ترشيح للمقابلة» (في كارت «قرار الموارد البشرية» أو من قائمة «قرار» فوق) ← اكتبي السبب ← «تأكيد»",
             "لو السبب فاضي الزرار بيترفض؛ بعد التأكيد الحالة بتتغير والقرار والسبب واسمك والوقت بيتسجلوا", png, time.time() - t)
        t = time.time()
        await open_applicant(hr, name)
        sel = await mark(hr, card("قرار الموارد البشرية|HR decision"))
        png = await snap(hr, "12_decision_done", sel)
        step(12, "القرار بعد التأكيد", f"{LAPTOP}/desk/job-applicant/{name}", HR, "لا شيء — الكارت بيتحدّث بعد التأكيد",
             "كارت «قرار الموارد البشرية» فيه الحالة الجديدة «Shortlisted» والسبب ومين قرر وإمتى؛ الذكاء ما غيّرش الحالة", png, time.time() - t)

        # 13 audit log
        t = time.time()
        await go(hr, "/desk/ai-recruitment-audit-log", "window.cur_list && cur_list.data")
        png = await snap(hr, "13_audit", await visible(hr))
        step(13, "سجل التدقيق", f"{LAPTOP}/desk/ai-recruitment-audit-log", HR, "من الرئيسية الزرار التاسع «سجل التدقيق»",
             "آخر الإجراءات فوق: القرار اللي لسه اتاخد بسببه، والتقييم، والمعالجة — كل سطر باسم صاحبه ووقته", png, time.time() - t)
        await hr.context.close()

        # 14 permissions: HR User refused on the settings
        t = time.time()
        u = await new_page(b, "1366", scale=1.5)
        await login(u, HRU, DEV["HR_USER_PASSWORD"])
        await u.goto(BASE + "/desk/ai-recruitment-settings")
        await settle(u, 3)
        png = await snap(u, "14_hr_user_refused", await visible(u))
        await u.context.close()
        step(14, "الصلاحيات: أخصائي التوظيف يحاول يفتح الإعدادات", f"{LAPTOP}/desk/ai-recruitment-settings", HRU, "سجّلي الخروج وادخلي بأخصائي التوظيف ثم افتحي الرابط (أو الزرار الثامن «الإعدادات» وهو رمادي)",
             "رسالة «لا يسمح لك بالوصول إلى هذه الصفحة»؛ الإعدادات والمفاتيح لمدير الموارد البشرية ومدير النظام بس", png, time.time() - t)

        # 15 engine down
        t = time.time()
        compose("stop", "api")
        try:
            hr2 = await new_page(b, "1366", scale=1.5)
            await login(hr2, HR, DEV["HR_MANAGER_PASSWORD"])
            await go(hr2, "/desk/ai-recruitment-settings", "window.cur_frm && cur_frm.doc", 3)
            await asyncio.sleep(2)
            png = await snap(hr2, "15_engine_down", await visible(hr2))
            await hr2.context.close()
        finally:
            compose("start", "api")
        for _ in range(60):
            try:
                import urllib.request

                if urllib.request.urlopen("http://127.0.0.1:18000/health", timeout=3).status == 200:
                    break
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(2)
        step(15, "حالة المحرك واقف", f"{LAPTOP}/desk/ai-recruitment-settings", HR, "(على السيرفر) `talent-engine/scripts/compose.sh stop api` ثم افتحي الإعدادات؛ وبعد العرض `… start api`",
             "كارت «حالة المحرك» بيقول إنه غير متاح؛ أي طلب يتقدّم في الوقت ده بيتحفظ عادي وبيتقيّم لما المحرك يرجع (لوحده كل ساعة أو بزرار «إعادة المحاولة»)", png, time.time() - t)

    md = ["# بروفة العرض — الخطوات بالترتيب", "", f"اتصوّرت بمتصفح حقيقي على الديمو النضيف. الروابط من اللابتوب عبر Tailscale. الوقت الكلي {round(time.time() - T0)} ثانية.", ""]
    for s in STEPS:
        md += [f"## {s['n']:02d} — {s['title']}", "", f"- الرابط: `{s['url']}`", f"- المستخدم: `{s['user']}`", f"- تدوسي على: {s['click']}", f"- النتيجة: {s['result']}",
               f"- الوقت في البروفة: {s['s']} ثانية", "", f"![{s['title']}]({s['png']})", ""]
    open(STEPS_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump(STEPS, open(os.path.join(ROOT, "demo", "steps.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(STEPS), "steps ->", STEPS_MD)


if __name__ == "__main__":
    asyncio.run(main())
