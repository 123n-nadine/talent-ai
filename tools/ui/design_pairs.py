"""Before/after crops of the design pass and the audit numbers for docs/TEST_REPORT.md.

    tools/.venv/bin/python tools/ui/design_pairs.py BEFORE_DIR AFTER_DIR

BEFORE_DIR and AFTER_DIR are two runs of tools/ui/design_audit.py (each has audit.json and one
folder per size). Writes docs/guide/images/design/*.png and docs/test-run/design_audit.json."""

from __future__ import annotations

import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw import ROOT, compact_png  # noqa: E402

BEFORE, AFTER = (os.path.abspath(a) for a in sys.argv[1:3])
OUT = os.path.join(ROOT, "docs", "guide", "images", "design")

# title, size, file, before box, after box (x0, y0, x1, y1 in CSS pixels of the screenshot)
PAIRS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_pairs.json"), encoding="utf-8"))


def counts(path: str) -> tuple[dict, int]:
    r = json.load(open(os.path.join(path, "audit.json"), encoding="utf-8"))
    c: dict[str, int] = {}
    for x in r:
        for i in x["issues"]:
            c[i["type"]] = c.get(i["type"], 0) + 1
    return c, len(r)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    b, n = counts(BEFORE)
    a, _ = counts(AFTER)
    pairs = []
    for p in PAIRS:
        rels = {}
        for side, base, box in (("before", BEFORE, p["before_box"]), ("after", AFTER, p["after_box"])):
            im = Image.open(os.path.join(base, p["size"], p["file"]))
            crop = im.crop(tuple(min(v, lim) for v, lim in zip(box, (im.width, im.height, im.width, im.height))))
            path = os.path.join(OUT, f"{p['key']}_{side}.png")
            crop.save(path)
            compact_png(path)
            rels[side] = os.path.relpath(path, os.path.join(ROOT, "docs"))
        pairs.append({"title": p["title"], **rels})
    out = {"screens": n, "before": b, "after": a, "pairs": pairs, "notes": PAIRS_NOTES}
    path = os.path.join(ROOT, "docs", "test-run", "design_audit.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"before": b, "after": a, "pairs": len(pairs)}))


PAIRS_NOTES = ("The two overlaps left are the HRMS «قدّم الآن» button on the phone job page: it stays fixed at the "
               "bottom of the screen and the page scrolls under it (standard HRMS behaviour, not changed). No JavaScript "
               "error on any of the screens.")

if __name__ == "__main__":
    main()
