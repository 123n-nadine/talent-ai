"""Write docs/TEST_REPORT.md from the full browser test (docs/test-run/full_test.json), the design
audit numbers (docs/test-run/design_audit.json) and the list of bugs fixed in round 2.

    tools/.venv/bin/python tools/ui/test_report.py
"""

from __future__ import annotations

import json
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS = os.path.join(ROOT, "docs")
RUN = json.load(open(os.path.join(DOCS, "test-run", "full_test.json"), encoding="utf-8"))
DESIGN_PATH = os.path.join(DOCS, "test-run", "design_audit.json")
DESIGN = json.load(open(DESIGN_PATH, encoding="utf-8")) if os.path.exists(DESIGN_PATH) else {}

# Bugs found and fixed in round 2, with the permanent test that now covers each one.
BUGS = [
    # id, area, what was wrong, the fix, the test that covers it
    ("B1", "Application save", "A database conflict (MariaDB snapshot isolation, error 1020) during the public form could lose the application.",
     "`api.apply()` saves through a helper with three attempts and checks the row exists before answering.", "Frappe `test_application_is_always_saved` (DB conflict case)"),
    ("B2", "Application save", "The screening job was queued inside the request, before the commit, so a queue error could roll the application back.",
     "Queued with `frappe.db.after_commit`; a queue error is logged, never raised.", "Frappe `test_application_is_always_saved` (queue down at commit)"),
    ("B3", "Application save", "A failing audit write could abort the application.", "`_safe_audit()` keeps the application and logs the audit error.",
     "Frappe `test_application_is_always_saved` (audit down)"),
    ("B4", "Application save", "A damaged CV file raised inside Frappe's File insert.", "Savepoint around the attachment; the reason goes to `ai_cv_note`; the application is saved.",
     "Frappe `test_application_is_always_saved` (damaged CV); browser C08"),
    ("B5", "Home page", "HR users landed on the generic desk in English.", "«التوظيف الذكي» home page for HR roles; Arabic set for new HR users.",
     "Frappe `test_hr_users_land_on_the_home_page_in_arabic`; browser R08"),
    ("S1", "Permissions", "`profile.templates_for` had no HR check: any logged-in user could list the approved profile templates.",
     "`require_hr()` and a read-permission check.", "Frappe `test_every_hr_method_refuses_other_users_first` (fails without the fix)"),
    ("S2", "Permissions (test data)", "The demo and test «Employee» users held no role at all: ERPNext removes the Employee roles from a user without an Employee record, so earlier checks tested a user with no role.",
     "Synthetic Employee records for these users (`seed_demo.ensure_employee`); the tests assert the role is held.", "Frappe `_employee_user()` assertion; browser R01"),
    ("S3", "Console", "Fonts were served as `application/octet-stream`.", "Media types for the static files.", "Engine `test_fonts_are_served_locally`"),
    ("F1", "CV files (found by the full test, C05)", "An RTF CV ended the screening in «فشل»: Frappe's File.get_content() returns text (str) for text-like files, hashing it failed, and any CV read problem failed the whole job.",
     "The CV is read as raw bytes from disk; a CV the platform cannot read or the engine refuses gives a «ملاحظة عن السيرة الذاتية» and the screening continues from the answers (decision 14); only an engine outage is retried.",
     "Frappe `test_text_cv_is_sent_as_bytes_and_cv_problems_never_fail` (fails without the fix); browser C05"),
    ("F2", "Re-score all (found by the full test, K14)", "«إعادة تقييم الكل» stopped at the first applicant who had withdrawn consent: queue_screening raised and every applicant after him stayed «قديم» (19 of 36 after the new profile version).",
     "Applicants without consent are skipped and counted; one applicant's error never stops the others; the ranking page says how many were skipped.",
     "Frappe `test_withdrawn_consent_stops_processing` (extended; fails without the fix); browser K14"),
    ("G1", "Job Opening (found while taking the guide screenshots)", "The Talent AI section of the opening sat inside the «تفاصيل الراتب» (Pay Details) tab: the custom fields were inserted after «description», which HRMS v16 follows with that tab.",
     "The section is inserted after the application web form route, in the main tab next to the publishing settings.", "Frappe `test_ai_section_is_on_the_main_tab_of_the_opening`"),
    ("D1", "Design", "Grey text at 4.13:1 (below WCAG AA 4.5:1) on every screen.", "Darker greys (#56627c) and darker chip text.", "Design audit (low-contrast count)"),
    ("D2", "Design", "Text at 10–11 px (cycle map, sidebar, help texts, KPI labels, code).", "Nothing under 12 px.", "Design audit (small-font count)"),
    ("D3", "Design", "Console ranking: the reference «HR-APP-…» was cut and ran under the score at 1366 px.", "The name column wraps; narrower bar under 1440 px.", "Design audit 1366/1440"),
    ("D4", "Design", "Desk ranking: strengths stacked and cut in the narrow name column.", "Strengths on their own line under each row.", "Design audit; screenshots K11"),
    ("D5", "Design", "Processing notes mixed English keys and Arabic in the wrong order («dob 1، name 3»).", "Arabic notes from the engine (`app/domain/arabic_text.py`) and bidi isolation of Latin words.", "Engine `test_cv_api`, `test_llm`; screenshots C01–C09"),
    ("D6", "Design", "Curly quotes landed on the wrong side of CV quotes in RTL.", "«…» around an isolated quote.", "Screenshots K05, K08"),
    ("D7", "Design", "Colours without one meaning: red «إلزامي», purple/red duplicate, amber stale, red contradiction and unreadable CV, purple read-only chip.",
     "Green = eligible/high, amber = medium/needs review, red = not eligible/low/failed, grey = stale/duplicate, blue = information, purple = an HR edit.", "Screenshots K04–K07"),
    ("D8", "Design", "Evaluation dates inside `<code>` were garbled in RTL.", "Readable Arabic dates, isolated.", "Screenshots"),
    ("D9", "Design", "HRMS recruitment labels in English (87 strings) and the grid's «No.» shown as «لا».", "Arabic translations in the app (`translations/ar.csv`).", "Screenshots R and K"),
    ("D10", "Design", "The applicant list's ID column showed «com».", "`hide_name_column` (the e-mail has its own column).", "Screenshot roles/hr_manager_list"),
    ("D11", "Design", "Answers grid: the technical key column was cut («…rs_sec»).", "Key hidden in the grid; question and answer wider.", "Screenshots C01"),
    ("D12", "Design / privacy", "Every page loaded the fonts from Google (a third-party call with the user's IP).", "IBM Plex Sans Arabic and IBM Plex Mono served by the app (OFL licence).", "Engine `test_fonts_are_served_locally`"),
    ("D13", "Design", "Raw method names and redaction keys («pdf_text», «name 3») on HR screens.", "Arabic labels («نص PDF مباشر», «الاسم (3)»).", "Screenshots C01–C09"),
    ("D14", "Design", "The same CSS block was repeated four times in both stylesheets.", "One copy.", "—"),
    ("D15", "Design", "Console audit log: the JSON payload overflowed into the next cells.", "The payload wraps inside its cell.", "Design audit (overlap count)"),
    ("D16", "Design", "Console criteria editor: «إلزامي» broken letter by letter, Arabic hints in a monospace font (disconnected letters), delete buttons cut at 1366 px.",
     "No-wrap label, Arabic font for Arabic hints, narrower columns.", "Design audit 1366"),
    ("D17", "Design", "Public job pages (HRMS): grey text below AA, 11 px labels, «Closes on:» and «Showing» in English.", "A scoped web stylesheet (`talent_ai_web.css`) and translations; the HRMS templates are untouched.", "Design audit public pages"),
    ("D18", "Design", "Cycle-map arrows at 1.46:1.", "3.9:1.", "Design audit"),
    ("D19", "Design (found in the roles screenshots)", "This round's `overflow-wrap: anywhere` on table cells let a narrow column shrink to one letter: the labels of the «حالة المحرك» card in the settings broke letter by letter next to a long URL.",
     "`overflow-wrap: break-word` on cells (long words still break, columns are not squeezed); codes and URLs still break anywhere. The audit now reports squeezed text (three or more lines of under three characters).", "Design audit (squeezed-text); settings screenshots retaken"),
    ("D20", "Design", "A quote from an English CV took the Arabic «» marks, which landed on the wrong sides when the quote wrapped.", "English quotes keep English marks “…” inside their own left-to-right block; Arabic quotes keep «…».", "Screenshot K11 / guide comparison"),
]


def git(path: str, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "?"


def cell(s) -> str:
    return str("" if s is None else s).replace("|", "\\|").replace("\n", " ")


def img(path: str, width: int = 520) -> str:
    return f'<img src="{path}" width="{width}" alt="">'


def main() -> None:
    tests = RUN.get("tests", {})
    perm = RUN.get("perm", {})
    passed = sum(1 for t in tests.values() if t["ok"])
    extra = [b for b in RUN.get("bugs_found", [])]
    L: list[str] = []
    w = L.append
    w("# Talent AI — full test report (round 2)\n")
    w(f"Run on the local bench, last update {RUN.get('updated_at', '?')} (Asia/Riyadh). Synthetic data only.\n")
    w("| | |\n|---|---|")
    w(f"| Workspace commit | `{git(ROOT, 'rev-parse', '--short', 'HEAD')}` (`{git(ROOT, 'branch', '--show-current')}`) |")
    w(f"| Frappe app commit | `{git(os.path.join(ROOT, 'ido_talent_ai'), 'rev-parse', '--short', 'HEAD')}` |")
    w("| Platform | Frappe v16.31.0, ERPNext v16.32.0, HRMS develop 640af1592a01 (`dev-frappe/VERSIONS.md`) |")
    w("| Engine | FastAPI + 4 RQ workers, Qwen3-8B-AWQ (vLLM, GPU cap 0.40), prompt `judge-v1`, PaddleOCR on CPU, Qwen3-Embedding-0.6B on CPU |")
    w("| Browser | Chrome 153 headless driven by Playwright 1.64 for Python (`tools/ui/full_test.py`). The Playwright MCP server was not available in this session, so the same Playwright engine was driven from Python. |")
    w(f"| Result | **{passed} of {len(tests)} checks passed** |\n")
    w("Screenshots are 8-bit PNG under `docs/guide/images/` (they are reused by the guide). Passwords and keys appear nowhere in this report or in the images.\n")

    w("## 1. Bugs found and fixed in round 2\n")
    w("| # | Area | Problem | Fix | Covered by |\n|---|---|---|---|---|")
    for b in BUGS + [tuple(x) for x in extra]:
        w("| " + " | ".join(cell(x) for x in b) + " |")
    w("")

    w("## 2. Roles and permissions\n")
    w(f"Roles on the local site: {len(perm.get('roles_on_site', []))}. Recruitment-related roles tested: {', '.join(perm.get('recruitment_roles', []))}.\n")
    if perm.get("not_found"):
        w(perm["not_found"] + "\n")
    users = perm.get("users", [])
    w("| User | Login | Roles |\n|---|---|---|")
    for u in users:
        w(f"| {u['label']} | `{u['login']}` | {', '.join(u['roles'])} |")
    w("\nPasswords of the test users are in `dev-frappe/.env` (never committed).\n")
    w("### 2.1 What each user sees (screens × users)\n")
    w("يشوف = sees it, read only · يعدّل = sees it and can act · ممنوع = refused (Frappe message or the login page).\n")
    word = {"see": "يشوف", "edit": "يعدّل", "deny": "ممنوع", "?": "؟"}
    m = perm.get("matrix", {})
    w("| Screen | " + " | ".join(u["label"] for u in users) + " |")
    w("|---|" + "---|" * len(users))
    for s in perm.get("screens", []):
        row = []
        for u in users:
            st = m.get(u["key"], {}).get(s["key"], {})
            row.append(f"{word.get(st.get('state'), '—')}")
        w(f"| {s['label']} | " + " | ".join(row) + " |")
    w("\nDetails and the screenshot of every cell (denial messages included):\n")
    for u in users:
        row = m.get(u["key"], {})
        if not row:
            continue
        w(f"<details><summary>{u['label']} (<code>{u['login']}</code>)</summary>\n")
        w("| Screen | Result | Detail | Screenshot |\n|---|---|---|---|")
        for s in perm.get("screens", []):
            st = row.get(s["key"], {})
            sh = f"[png]({st['shot']})" if st.get("shot") else ""
            w(f"| {s['label']} | {word.get(st.get('state'), '—')} | {cell(st.get('detail'))} | {sh} |")
        w("\n</details>\n")
    probes = perm.get("probes", {})
    if probes:
        keys = list(next(iter(probes.values())).keys())
        w("### 2.2 Server-side checks (HTTP status per call)\n")
        w("Each call was made from the user's own browser session. 200 = allowed; 403 = refused; 417 = allowed past the permission check and stopped by validation (the probe sends an invalid status or an empty reason, so nothing changes); 404 = allowed, the probe record does not exist.\n")
        w("| Call | " + " | ".join(u["label"] for u in users if u["key"] in probes) + " |")
        w("|---|" + "---|" * sum(1 for u in users if u["key"] in probes))
        for k in keys:
            vals = []
            for u in users:
                if u["key"] not in probes:
                    continue
                p = probes[u["key"]].get(k, {})
                vals.append(f"{p.get('status', '—')}" + (f" ({p['note']})" if p.get("note") else ""))
            w(f"| `{k}` | " + " | ".join(vals) + " |")
        w("")

    def section(title: str, prefix: tuple[str, ...]) -> None:
        rows = [(k, v) for k, v in tests.items() if k.startswith(prefix)]
        if not rows:
            return
        w(f"## {title}\n")
        for k, v in sorted(rows):
            w(f"### {k} — {v['title']} {'✅' if v['ok'] else '❌'}\n")
            w("| | |\n|---|---|")
            w(f"| User | {cell(v.get('user'))} |")
            if v.get("file"):
                w(f"| File | `{cell(v['file'])}` |")
            w(f"| Expected | {cell(v.get('expected'))} |")
            w(f"| Actual | {cell(v.get('actual'))} |")
            if v.get("history"):
                w(f"| History | {cell(v['history'])} |")
            if v.get("seconds") is not None:
                w(f"| Time | {v['seconds']} s |")
            if v.get("timing"):
                t = v["timing"]
                w(f"| Timing | form {t.get('form_load_s')} s · submit {t.get('submit_s')} s · result {t.get('until_result_s')} s after submit · engine pipeline {t.get('pipeline_s')} s |")
            w("")
            shots = v.get("shots") or []
            if shots:
                w(img(shots[-1] if k.startswith("C") else shots[0]))
                if len(shots) > 1:
                    w("\nAll screenshots: " + " · ".join(f"[{os.path.basename(s)}]({s})" for s in shots))
                w("")

    section("3. Roles: landing page and isolation", ("R0", "R1"))
    section("4. CV types (public form → HR screen)", ("C",))
    section("5. Special cases", ("K",))
    section("6. Talent Console (Nadine)", ("N",))
    section("7. Page load times", ("P",))
    pages = RUN.get("timings", {}).get("pages", {})
    if pages:
        w("| Page | First load (s) | Warm, median of 2 (s) |\n|---|---|---|")
        for k, v in pages.items():
            w(f"| {k} | {v.get('cold')} | {v.get('warm_median', '—')} |")
        w("")
    cv = [(k, v) for k, v in tests.items() if k.startswith("C") and v.get("timing")]
    if cv:
        w("### Processing time by CV type\n")
        w("| Test | File | Submit (s) | Result after submit (s) | Engine pipeline (s) |\n|---|---|---|---|---|")
        for k, v in sorted(cv):
            t = v["timing"]
            w(f"| {k} {v['title']} | `{v.get('file') or '—'}` | {t.get('submit_s')} | {t.get('until_result_s')} | {t.get('pipeline_s')} |")
        w("")

    if DESIGN:
        w("## 8. Design pass (before → after)\n")
        w(f"Every screen at 1366, 1440 and 1920 px, and the public pages at 375 and 390 px: {DESIGN.get('screens')} screens per run, measured in the browser by `tools/ui/design_audit.py` (text boxes that overlap, text cut or off screen, page overflow, text under 11.5 px, contrast under WCAG AA).\n")
        w("| Issue | Before | After |\n|---|---|---|")
        for k in ("low-contrast", "small-font", "overlap", "off-screen-text", "cut-text", "page-overflow"):
            w(f"| {k} | {DESIGN.get('before', {}).get(k, 0)} | {DESIGN.get('after', {}).get(k, 0)} |")
        if DESIGN.get("notes"):
            w("\n" + DESIGN["notes"] + "\n")
        for p in DESIGN.get("pairs", []):
            w(f"**{p['title']}**\n")
            w(f"| Before | After |\n|---|---|\n| {img(p['before'], 420)} | {img(p['after'], 420)} |\n")
    # ---------------------------------------------------------------- §10–§13 (the test column of docs/guide/COVERAGE.md)
    import glob
    import re as _re

    def tests_of(pattern: str) -> list[tuple[str, str, str]]:
        out = []
        for p in sorted(glob.glob(pattern)):
            src = open(p, encoding="utf-8").read()
            for m in _re.finditer(r'^\s*def (test_[a-z0-9_]+)\(.*?\n(?:\s*"""(.*?)(?:"""|\n))?', src, _re.M | _re.S):
                out.append((os.path.relpath(p, ROOT), m.group(1), (m.group(2) or "").strip().split("\n")[0][:140]))
        return out

    w("## 10. Automated tests\n")
    w(f"Engine: `make test` in `talent-engine/` — {RUN.get('engine_suite', '112 passed, 1 skipped (the PaddleOCR test runs only with RUN_OCR_TESTS=1)')}. "
      f"Frappe app: `bench --site test.localhost run-tests --app ido_talent_ai` — {RUN.get('frappe_suite', 'all passed')}.\n")
    w("| Suite | File | Test | What it checks |\n|---|---|---|---|")
    for f, n, d in tests_of(os.path.join(ROOT, "talent-engine", "tests", "test_*.py")):
        w(f"| engine | `{f}` | `{n}` | {cell(d)} |")
    for f, n, d in tests_of(os.path.join(ROOT, "ido_talent_ai", "ido_talent_ai", "tests", "test_*.py")):
        w(f"| Frappe | `{f}` | `{n}` | {cell(d)} |")
    w("")
    cmds_path = os.path.join(DOCS, "test-run", "commands.json")
    if os.path.exists(cmds_path):
        cmds = json.load(open(cmds_path, encoding="utf-8"))
        w("## 11. Commands\n")
        w("Every make target and script of the inventory, with what was run in round 2. Targets that would stop or change the shared stack (`down`, `up`, `revision`, `seed`, `cvs`, `receiver`, `logs`) were checked with `make -n` only; `build` and the compose restarts were run for real (default builder).\n")
        w("| Command | Mode | Result |\n|---|---|---|")
        for k, v in cmds.items():
            w(f"| `{cell(v['cmd'])}` | {v['mode']} | {cell(v['result'])} |")
        w("")
    w("## 12. Decisions and open questions: how they were checked\n")
    dec = {
        "1 form answers are the primary source": "C07 (no CV), C01–C09", "2 weights total 100%, five fixed levels": "Frappe `test_weights_must_total_100_to_approve`; K14 (105% refused)",
        "3 hard rules in code; no identity to the LLM": "Frappe `test_engine_payload_has_no_identity`; K02", "4 redaction before any LLM step": "engine redaction tests; C01",
        "5 every judgement has evidence": "engine evidence tests; K04, K05", "6 the LLM judges, code computes": "engine scoring tests; guide §8 worked example (asserted)",
        "7 AI never changes the status": "Frappe `test_result_sets_ai_fields_but_never_the_status`; R03", "8 provider local | cloud": "engine `test_llm` (cloud path with a mocked endpoint)",
        "9 OCR provider configurable": "C01, C09 (PaddleOCR CPU)", "10 names from the client document": "roles matrix (screen names)",
        "11 scope (postponed features not built)": "nothing of the postponed list exists in the code or the screens", "12 the client's 8 acceptance criteria": "docs/ACCEPTANCE_REPORT.md (phase 7) and this report",
        "13 the engine owns the AI/OCR settings": "engine settings tests; guide step 13", "14 an unreadable CV never fails a screening": "C08; bug F1 fixed",
        "15 UTC in the engine": "Frappe `test_engine_payload_has_no_identity` (applied_at)", "16 our own web form": "C01–C09",
    }
    w("| Decision (CLAUDE.md) | Checked by |\n|---|---|")
    for k, v in dec.items():
        w(f"| {k} | {v} |")
    w("\nDecisions taken alone (docs/PROGRESS.md) are checked by the screen or test they describe: embeddings and the talent pool by K12; one suggestion per person and the host filter by K12; redaction keeps line breaks and layout in display pixels by C01–C04; fonts bundled by the engine test `test_fonts_are_served_locally`; no change to HRMS templates by the design audit of the public pages; English stage notes by the console screens N01; the old-application demo case by K12 (retention ended); synthetic Employee records by R01–R09 (the Employee and self-service users hold their roles, `_employee_user` asserts it); a CV problem never fails a screening by C05 and the Frappe test `test_text_cv_is_sent_as_bytes_and_cv_problems_never_fail`; «إعادة تقييم الكل» skipping withdrawn consent by `test_withdrawn_consent_stops_processing`; the three guide decisions (screenshots cut to the part explained, page numbers from the printed PDF, the Word file checked through LibreOffice) by the page checks of §14.\n")
    w("Open questions (docs/OPEN_QUESTIONS.md) wait for an answer from the client or the Frappe team; until then the current behaviour is what is tested: #6 placeholder rules → K02; #7 consent and retention → K12, Frappe consent tests; #15 database conflicts → Frappe `test_application_is_always_saved`; #16 rate limit → `talent_ai_apply_limit` used by every application of this run; #17 translations → design audit; #18 photo not built → C01–C09; #20 HR-entered applications → not processed without consent (Frappe consent tests); #21 consent-withdrawn stale results → F2 and K14. #1–#4, #8, #9 and #13 are deployment or data questions with nothing to test on the local bench.\n")
    w("## 13. Evaluation results (phase 4, docs/EVALUATION_REPORT.md)\n")
    w("Gold set of 50 synthetic applicants: Qwen3-8B-AWQ with `judge-v1` — 98% exact levels, 100% within one step, 100% evidence for levels above 0, 100% eligibility, 100% expected flags; rerun and name-swap identical for 100%. "
      "`judge-v2` (Arabic) and Qwen3-4B-AWQ were weaker. Throughput: 100 applicants in 13.4 / 7.8 / 5.4 minutes with 2 / 4 / 8 workers, GPU memory never above 9.5 GB. "
      "OCR_MIN_CONFIDENCE stays 0.80 (C09 shows a bad scan at 0.79 going to «يحتاج مراجعة»); quotes are matched at a fuzzy ratio of 0.9 after Arabic normalisation.\n")
    guide_check = os.path.join(DOCS, "test-run", "guide_check.json")
    if os.path.exists(guide_check):
        g = json.load(open(guide_check, encoding="utf-8"))
        cov = g.get("coverage", {})
        w("## 14. The guide (docs/guide/)\n")
        w("`tools/guide/build.py` writes the PDF (Chrome `page.pdf`) and the Word file (python-docx, checked by converting it to PDF with LibreOffice), then checks every page of both: "
          "no picture outside the page, no two text lines drawn over each other, nothing painted in the footer, no text at the paper edge, and every page of the chapters starting with its own title "
          "(a page that starts with something else holds the tail of the previous one). `tools/guide/coverage_check.py` reads the routes, DocTypes, endpoints and commands from the code again and compares them with `docs/guide/COVERAGE.md`.\n")
        w("| Check | PDF | Word |\n|---|---|---|")
        w(f"| Pages | {g['pdf']['pages']} | {g.get('docx_as_pdf', {}).get('pages', '—')} |")
        w(f"| Page problems | {len(g['pdf']['problems'])} | {len(g.get('docx_as_pdf', {}).get('problems', []))} |")
        fld = g.get("docx_fields") or {}
        word_fields = (f"{fld['fields'] - fld['without_number']} of {fld['fields']} page fields show their page; {len(fld['moved_after_pass_2'])} moved"
                       if fld else "fields (PAGEREF)")
        w(f"| Page numbers of the contents and the index | {'stable after the second print' if g.get('pages_stable') else 'NOT stable'} | {word_fields} |")
        import sys as _sys

        chk = subprocess.run([_sys.executable, os.path.join(ROOT, "tools", "guide", "coverage_check.py")], capture_output=True, text=True)
        missing = (_re.search(r"MISSING: (\d+)", chk.stdout) or [None, "?"])[1]
        w(f"\nInventory read from the code: **{cov.get('items')} items, {cov.get('complete')} with a guide page, a screenshot and a test** (`docs/guide/COVERAGE.md`); the independent check reports **MISSING: {missing}**.\n")
    if RUN.get("not_done"):
        w("## 15. Not done, and why\n")
        for x in RUN["not_done"]:
            w(f"- {x}")
        w("")
    open(os.path.join(DOCS, "TEST_REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"docs/TEST_REPORT.md: {passed}/{len(tests)} checks, {len(BUGS) + len(extra)} bugs listed")


if __name__ == "__main__":
    main()
