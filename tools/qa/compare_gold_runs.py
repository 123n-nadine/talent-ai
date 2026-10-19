"""Compare the two latest gold-set runs in the engine database, judgement by judgement: which
levels changed, split into code-levelled and model-judged (free text, CV side). Read-only.

    tools/.venv/bin/python tools/qa/compare_gold_runs.py  [hours-back]
"""

from __future__ import annotations

import collections
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
HOURS = sys.argv[1] if len(sys.argv) > 1 else "36"

QUERY = f'''
import json
from sqlalchemy import text
from app.core.config import get_settings
from app.storage.db import make_engine
e = make_engine(get_settings().database_url)
with e.connect() as c:
    rows = c.execute(text("""select c.external_ref, s.id, s.created_at, s.status
        from screenings s join candidates c on c.id=s.candidate_id
        where c.external_ref like 'GOLD-%' and s.created_at > now() - interval '{HOURS} hours' order by s.created_at""")).all()
    scr = [{{"ref": r[0], "id": r[1], "at": str(r[2]), "status": r[3]}} for r in rows]
    lv = c.execute(text("select screening_id, criterion_key, level, source, contradiction from criterion_results where screening_id = any(:ids)"), {{"ids": [s["id"] for s in scr]}}).all()
print(json.dumps({{"scr": scr, "lv": [list(r) for r in lv]}}, default=str))
'''


def main() -> None:
    out = subprocess.run(["docker", "exec", "-i", "talentai-api-1", "python", "-"], input=QUERY, capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    gold = {}
    for f in ("security_supervisor.json", "data_analyst.json"):
        for a in json.load(open(os.path.join(ROOT, "talent-engine", "eval", "gold", f), encoding="utf-8"))["applicants"]:
            gold[a["ref"]] = a
    # runs = clusters of screenings by time: a new run starts when the first ref appears again
    runs: list[dict[str, dict]] = []
    seen: set[str] = set()
    cur: dict[str, dict] = {}
    for s in d["scr"]:
        if s["ref"] in seen:
            runs.append(cur)
            cur, seen = {}, set()
        cur[s["ref"]] = s
        seen.add(s["ref"])
    if cur:
        runs.append(cur)
    # name-swap passes re-screen only the CV applicants: keep the passes that cover (almost) all refs
    full = [r for r in runs if len(r) >= 50]
    if len(full) < 2:
        print("need two full runs, found", len(full), "(all passes:", [len(r) for r in runs], ")")
        return
    before, after = full[-2], full[-1]
    levels: dict[str, dict] = collections.defaultdict(dict)
    for sid, key, level, src, contra in d["lv"]:
        levels[sid][key] = (level, src, contra)
    changed_code, changed_model, n_code, n_model = [], [], 0, 0
    for ref in sorted(set(before) & set(after)):
        a = gold[ref]
        model_keys = {"project"} if ref.startswith("GOLD-ANA") else set()
        if a["archetype"] == "contradiction":
            model_keys |= {"supervision"}
        lb, la = levels[before[ref]["id"]], levels[after[ref]["id"]]
        for key in sorted(set(lb) | set(la)):
            b, x = lb.get(key), la.get(key)
            by_model = key in model_keys or (x and x[1] == "cv_quote") or (b and b[1] == "cv_quote")
            if by_model:
                n_model += 1
            else:
                n_code += 1
            if (b or (None,))[0] != (x or (None,))[0]:
                (changed_model if by_model else changed_code).append((ref, key, b and b[0], x and x[0], a["expected"]["levels"].get(key)))
    print(f"before: {min(s['at'] for s in before.values())[:16]} ({len(before)} applicants) | after: {min(s['at'] for s in after.values())[:16]} ({len(after)} applicants)")
    print(f"code-levelled judgements: {n_code}, changed {len(changed_code)}; model-judged: {n_model}, changed {len(changed_model)}")
    for ref, key, b, x, exp in changed_code + changed_model:
        print(f"  {ref} {key}: {b} -> {x} (expected {exp})")


if __name__ == "__main__":
    main()
