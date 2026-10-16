"""Commands run for the record (docs/test-run/commands.json) and pictures of documents without a
screen of their own (docs/guide/images/terminal/): the make targets with their results, the
project decisions, the evaluation tables, the open questions and the settings files with their
keys only (no value, so no password or key can appear in a picture).

    tools/.venv/bin/python tools/guide/docshots.py
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui"))
from pw import ROOT, compact_png  # noqa: E402

ENG = os.path.join(ROOT, "talent-engine")
OUT = os.path.join(ROOT, "docs", "guide", "images", "terminal")
REAL = ["builder-check", "install", "test", "lint", "fmt", "typecheck", "gpu", "ps", "migrate"]
DRY = ["build", "env", "up", "down", "logs", "llm-logs", "revision", "seed", "cvs", "receiver"]
ROUND2 = {  # scripts used during round 2 (this run)
    "talent-engine/scripts/compose.sh": "restart of api and workers", "dev-frappe/reset_demo.sh": "demo rebuilt (25 applicants)",
    "dev-frappe/init_env.sh": "extra test-user passwords added", "dev-frappe/start.sh": "bench restarted twice", "dev-frappe/setup.sh": "run inside reset_demo (site setup)",
    "tools/ui/full_test.py": "full browser test", "tools/ui/design_audit.py": "3 design audits", "tools/ui/design_pairs.py": "before/after pairs",
    "tools/ui/pw.py": "used by every browser tool", "tools/ui/test_report.py": "docs/TEST_REPORT.md", "tools/ui/apply_via_form.py": "applicant 2017 through the real form",
    "ido_talent_ai/ido_talent_ai/scripts/seed_demo.py": "demo setup and test users", "ido_talent_ai/ido_talent_ai/scripts/submit_demo_applications.py": "24 applications",
    "tools/guide/facts.py": "guide numbers", "tools/guide/shots.py": "guide screenshots", "tools/guide/build.py": "guide build", "tools/guide/inventory.py": "inventory",
    "tools/guide/lint_ar.py": "writing rules", "tools/guide/inv.py": "item codes", "tools/guide/model.py": "guide content model", "tools/guide/render_html.py": "PDF",
    "tools/guide/render_docx.py": "Word", "tools/guide/docshots.py": "this file", "tools/guide/coverage_check.py": "coverage check",
}
EARLIER = {
    "tools/ui/acceptance.py": "phase 7 (docs/ACCEPTANCE_REPORT.md)", "tools/ui/walkthrough_shots.py": "phase 8 (docs/WALKTHROUGH.md)", "tools/ui/desk_shots.py": "phase 6",
    "tools/ui/frappe_ui.py": "phases 6–8 (CDP driver of the older tools)", "talent-engine/scripts/callback_receiver.py": "phase 1 (HMAC callback verified)",
    "talent-engine/scripts/make_cvs.py": "phase 2 (`make cvs`)", "talent-engine/scripts/cv_texts.py": "phase 2", "talent-engine/scripts/seed.py": "phase 1 (`make seed`)",
    "talent-engine/scripts/seed_data.py": "phase 1", "talent-engine/scripts/init_env.py": "phase 1 (`make env`)", "talent-engine/eval/run.py": "phase 4 (docs/EVALUATION_REPORT.md)",
    "talent-engine/eval/bench.py": "phase 4", "talent-engine/eval/make_gold.py": "phase 4", "dev-frappe/clean_install.sh": "phase 7 (clean install rehearsal)",
}


def run(cmd: list[str], cwd: str, timeout: int = 900) -> dict:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout + p.stderr).strip().splitlines()
        return {"exit": p.returncode, "tail": out[-6:]}
    except subprocess.TimeoutExpired:
        return {"exit": "timeout", "tail": []}


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    cmds: dict[str, dict] = {}
    for t in REAL:
        r = run(["make", t], ENG)
        cmds[f"make:{t}"] = {"cmd": f"make {t}", "result": "ok" if r["exit"] == 0 else f"exit {r['exit']}", "tail": r["tail"], "mode": "run"}
        print("make", t, r["exit"], flush=True)
    for t in DRY:
        r = run(["make", "-n", t], ENG)
        cmds[f"make:{t}"] = {"cmd": f"make -n {t}", "result": "dry run ok" if r["exit"] == 0 else f"exit {r['exit']}", "tail": r["tail"], "mode": "dry run"}
    cmds["make:build"]["result"] += "; built for real this round (default builder)"
    for path, why in ROUND2.items():
        cmds[f"script:{path}"] = {"cmd": path, "result": f"run in round 2: {why}", "tail": [], "mode": "run"}
    for path, why in EARLIER.items():
        cmds[f"script:{path}"] = {"cmd": path, "result": f"run in {why}", "tail": [], "mode": "earlier"}
    for c in ("bench --site <site> migrate", "bench --site <site> run-tests --app ido_talent_ai"):
        cmds[f"bench:{c}"] = {"cmd": c, "result": "run in round 2 on talent.localhost and test.localhost", "tail": [], "mode": "run"}
    for c in ("bench get-app", "bench --site <site> install-app ido_talent_ai", "bench --site <site> uninstall-app ido_talent_ai"):
        cmds[f"bench:{c}"] = {"cmd": c, "result": "run in phase 7 clean install rehearsal; install-app also by reset_demo.sh in round 2", "tail": [], "mode": "run"}
    json.dump(cmds, open(os.path.join(ROOT, "docs", "test-run", "commands.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    asyncio.run(pictures(cmds))


def keys_only(path: str) -> str:
    out = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
        if m:
            out.append(f"{m.group(1)}=…")
        elif line.startswith("#"):
            out.append(line.rstrip())
    return "\n".join(out)


async def pictures(cmds: dict) -> None:
    from playwright.async_api import async_playwright

    docs = {
        "commands": ("الأوامر ونتيجتها في الجولة التانية", "\n".join(f"{v['cmd']:<52} {v['result']}" for k, v in cmds.items() if k.startswith(("make:", "bench:")))),
        "decisions": ("قرارات المشروع الثابتة (CLAUDE.md)", re.sub(r"\n{2,}", "\n", open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read().split("## Decisions already made")[1].split("## Hard rules")[0]).strip()),
        "evaluation": ("نتائج التقييم (EVALUATION_REPORT.md)", open(os.path.join(ROOT, "docs", "EVALUATION_REPORT.md"), encoding="utf-8").read().split("## 3.")[0].strip()),
        "open_questions": ("الأسئلة المفتوحة (OPEN_QUESTIONS.md)", open(os.path.join(ROOT, "docs", "OPEN_QUESTIONS.md"), encoding="utf-8").read().split("## Answered")[0].strip()),
        "env_keys": ("ملفات الإعدادات: الأسماء بس، من غير أي قيمة", "# talent-engine/.env.example\n" + keys_only(os.path.join(ENG, ".env.example")) + "\n\n# dev-frappe/.env.example\n" + keys_only(os.path.join(ROOT, "dev-frappe", ".env.example"))),
    }
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 1500, "height": 900}, device_scale_factor=1.3)
        for name, (title, text) in docs.items():
            body = html.escape(text)
            await pg.set_content(f"""<html><body style="margin:0;background:#0f1a33">
              <div style="font-family:'IBM Plex Sans Arabic',sans-serif;direction:rtl;color:#fff;background:#1e4db5;padding:10px 16px;font-size:18px">{html.escape(title)}</div>
              <pre id="t" style="margin:0;padding:14px 18px;color:#e7eeff;font:13px/1.55 'IBM Plex Mono',Consolas,monospace;white-space:pre-wrap;direction:ltr;unicode-bidi:plaintext">{body}</pre></body></html>""")
            path = os.path.join(OUT, name + ".png")
            await pg.screenshot(path=path, full_page=True)
            compact_png(path)
            print("picture", name, flush=True)
        await b.close()


if __name__ == "__main__":
    main()
