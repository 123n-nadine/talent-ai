"""Bidi-aware text reconstruction for PDFs. PyMuPDF returns Arabic PDFs (LibreOffice/Word output)
as visual fragments: Latin/digit runs become separate lines and reading order breaks. We group
spans into rows by their vertical position and rebuild each row: Arabic rows run right-to-left,
Latin/digit runs inside them keep left-to-right order and are glued when the gap is tiny."""

from __future__ import annotations

import re
from typing import Any

ARABIC = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z0-9@]")


def page_spans(page: Any) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                t = sp.get("text", "")
                if not t.strip():
                    continue
                x0, y0, x1, y1 = sp["bbox"]
                spans.append(
                    {
                        "t": t,
                        "x0": x0,
                        "x1": x1,
                        "yc": (y0 + y1) / 2,
                        "h": max(y1 - y0, 1.0),
                        "size": float(sp.get("size", 10.0)),
                    }
                )
    return spans


def group_rows(spans: list[dict[str, Any]], tol: float = 0.5) -> list[list[dict[str, Any]]]:
    rows: list[list[dict[str, Any]]] = []
    for s in sorted(spans, key=lambda s: s["yc"]):
        if rows and abs(rows[-1][0]["yc"] - s["yc"]) < tol * rows[-1][0]["h"]:
            rows[-1].append(s)
        else:
            rows.append([s])
    return rows


def _join_run(group: list[dict[str, Any]], ltr: bool) -> str:
    """Join spans of one run; glue neighbours whose horizontal gap is smaller than ~a third of a char."""
    ordered = sorted(group, key=lambda s: s["x0"]) if ltr else sorted(group, key=lambda s: -s["x1"])
    out = ""
    prev = None
    for s in ordered:
        t = s["t"].strip()
        if prev is not None:
            gap = (s["x0"] - prev["x1"]) if ltr else (prev["x0"] - s["x1"])
            out += "" if gap < 0.3 * s["size"] else " "
        out += t
        prev = s
    return out


def row_text(row: list[dict[str, Any]]) -> str:
    row = sorted(row, key=lambda s: s["x0"])  # visual left -> right
    if not any(ARABIC.search(s["t"]) for s in row):
        return _join_run(row, ltr=True)
    runs: list[tuple[str, list[dict[str, Any]]]] = []
    for s in row:
        kind = "A" if ARABIC.search(s["t"]) else "L" if LATIN.search(s["t"]) else "N"  # N = neutral
        if runs and (runs[-1][0] == kind or (kind == "N" and runs[-1][0] == "L")):
            runs[-1][1].append(s)
        elif kind == "N" and runs and runs[-1][0] == "A":
            runs[-1][1].append(s)
        else:
            runs.append(("L" if kind == "N" else kind, [s]))
    parts = [_join_run(group, ltr=(kind == "L")) for kind, group in reversed(runs)]  # right -> left
    return " ".join(p for p in parts if p)


def reconstruct(page: Any) -> str:
    spans = page_spans(page)
    if not spans:
        return ""
    return "\n".join(row_text(r) for r in group_rows(spans))
