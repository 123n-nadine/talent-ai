"""Bidi-aware text reconstruction for PDFs.

Word and LibreOffice write Arabic pages in *visual* order: the glyphs of a line are placed from
left to right exactly as they appear on paper, so an Arabic sentence comes out reversed, a date
or an e-mail inside it keeps its left-to-right order, and the full stop of a sentence sits at the
far left. PyMuPDF partly undoes this per span, which is how a dot of an e-mail ended up at the end
of the line and a number glued to the word before it (round 3 review: "demo.2001@example com.",
"من14. فرد").

This module works at the character level instead: every character of a page comes with its box,
characters are grouped into rows by baseline, sorted by their position on the page (the visual
order) and turned back into logical order with the inverse of the bidi reordering:

- the base direction of a row with Arabic letters is right-to-left on an Arabic page (most rows
  hold Arabic) and left-to-right on a Latin page (an Arabic word inside an English CV);
- Latin letters and digits form left-to-right units; neutrals (spaces, punctuation) between two
  characters of the same kind belong to that kind, the others follow the base direction — with
  one exception taken from the bidi algorithm: between two numbers only a single separator
  (".", ",", ":", "/", "-") joins them (a date, a phone), a dash or a space does not;
- a right-to-left row is read from its right end, each left-to-right unit kept as it is; mirrored
  brackets are swapped back.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
MIRROR = str.maketrans("()[]{}<>«»", ")(][}{><»«")

Char = dict[str, Any]


def _ctype(c: str) -> str:
    """R = Arabic letter, L = Latin letter or digit (a left-to-right unit), N = neutral."""
    if c in "٠١٢٣٤٥٦٧٨٩":
        return "L"  # digits are read left to right inside Arabic too
    if unicodedata.category(c).startswith("P"):
        return "N"  # Arabic punctuation (، ؛ ؟) is neutral like any other
    if ARABIC.match(c):
        return "R"
    if c.isalnum():
        return "L"
    return "N"


def page_chars(page: Any) -> list[Char]:
    """Every character of the page with its box and baseline (PyMuPDF rawdict)."""
    out: list[Char] = []
    for block in page.get_text("rawdict").get("blocks", []):
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                size = float(sp.get("size", 10.0)) or 10.0
                for ch in sp.get("chars", []):
                    c = ch.get("c", "")
                    if not c or c == "\x00":
                        continue
                    x0, y0, x1, y1 = ch["bbox"]
                    unit = {
                        "c": c,
                        "x0": float(x0),
                        "x1": float(x1),
                        "y0": float(y0),
                        "y1": float(y1),
                        "yb": float(ch.get("origin", (0, y1))[1]),
                        "size": size,
                    }
                    # a ligature (lam-alef) or a mark comes as a second character without a box
                    # of its own: it stays glued to the character before it, in logical order
                    if (
                        out
                        and x1 - x0 < 0.05 * size
                        and ARABIC.match(c)
                        and abs(out[-1]["x0"] - x0) < 0.6 * size
                        and abs(out[-1]["yb"] - unit["yb"]) < 0.1 * size
                    ):
                        out[-1]["c"] += c
                        continue
                    out.append(unit)
    return out


def group_rows(chars: list[Char], tol: float = 0.45) -> list[list[Char]]:
    """Rows by baseline: a character joins the row whose baseline is within `tol` × font size."""
    rows: list[list[Char]] = []
    for ch in sorted(chars, key=lambda c: (c["yb"], c["x0"])):
        if rows and abs(rows[-1][-1]["yb"] - ch["yb"]) <= tol * max(
            ch["size"], rows[-1][-1]["size"]
        ):
            rows[-1].append(ch)
        else:
            rows.append([ch])
    return rows


def _visual(row: list[Char]) -> list[Char]:
    """The row in visual order: sorted by position, overlapping phantom spaces dropped, a space
    added where two characters are clearly apart but no space glyph was written."""
    ordered = sorted(row, key=lambda c: (c["x0"], c["c"].isspace()))
    kept: list[Char] = []
    for ch in ordered:
        if ch["c"].isspace():
            w = max(ch["x1"] - ch["x0"], 0.1)
            if any(
                not o["c"].isspace() and min(o["x1"], ch["x1"]) - max(o["x0"], ch["x0"]) > 0.5 * w
                for o in row
            ):
                continue  # a space placed over a real glyph (PyMuPDF keeps both)
            if kept and kept[-1]["c"].isspace():
                continue
        kept.append(ch)
    out: list[Char] = []
    for ch in kept:
        if out and not out[-1]["c"].isspace() and not ch["c"].isspace():
            gap = ch["x0"] - out[-1]["x1"]
            if gap > 0.28 * min(ch["size"], out[-1]["size"]):
                out.append({**ch, "c": " ", "x0": out[-1]["x1"], "x1": ch["x0"]})
        out.append(ch)
    return out


NUMBER_SEP = ".,:/-٫٬"


def _resolve_types(types: list[str], units: list[str], base: str) -> list[str]:
    """Neutrals between two characters of one kind take that kind, the others the base direction.
    Between two digits only a single separator joins them (bidi rule W4: "14/05/1992" is one
    number, "2017–2026" and "2017 2026" are two)."""
    n = len(types)
    out = list(types)
    i = 0
    while i < n:
        if out[i] != "N":
            i += 1
            continue
        j = i
        while j < n and out[j] == "N":
            j += 1
        before = out[i - 1] if i > 0 else None
        after = out[j] if j < n else None
        fill = before if (before is not None and before == after) else base
        if fill == "L" and 0 < i and j < n and units[i - 1][-1].isdigit() and units[j][0].isdigit():
            fill = "L" if (j - i == 1 and units[i] in NUMBER_SEP) else base
        for k in range(i, j):
            out[k] = fill
        i = j
    return out


def logical_text(visual: str | list[str], base: str | None = None) -> str:
    """Logical order of text given in visual (left-to-right on paper) order. `visual` is a
    string, or a list of units when some glyphs stand for several characters (a lam-alef
    ligature is one unit "لا" that keeps its own order)."""
    units = list(visual) if isinstance(visual, str) else [u for u in visual if u]
    if not units:
        return ""
    types = [_ctype(u[0]) for u in units]
    if base is None:  # without the page, a line with Arabic letters is taken as Arabic
        base = "R" if "R" in types else "L"
    types = _resolve_types(types, units, base)
    runs: list[tuple[str, list[str]]] = []
    for u, t in zip(units, types, strict=False):
        if runs and runs[-1][0] == t:
            runs[-1][1].append(u)
        else:
            runs.append((t, [u]))

    def text(t: str, us: list[str]) -> str:
        return "".join(reversed(us)).translate(MIRROR) if t == "R" else "".join(us)

    ordered = reversed(runs) if base == "R" else runs
    return "".join(text(t, us) for t, us in ordered)


def has_arabic(row: list[Char]) -> bool:
    return any(ARABIC.match(c["c"][0]) for c in row)


def page_is_arabic(rows: list[list[Char]]) -> bool:
    """A page is Arabic when most of its rows hold Arabic letters (an Arabic word inside an
    English CV then keeps the English reading direction, and the other way round)."""
    arabic = sum(1 for r in rows if has_arabic(r))
    return arabic >= len(rows) - arabic


def row_text(row: list[Char], arabic_page: bool = True) -> str:
    units = [c["c"] for c in _visual(row)]
    base = "R" if arabic_page and has_arabic(row) else "L"
    return re.sub(r" {2,}", " ", logical_text(units, base)).strip()


def row_box(row: list[Char]) -> tuple[float, float, float, float]:
    return (
        min(c["x0"] for c in row),
        min(c["y0"] for c in row),
        max(c["x1"] for c in row),
        max(c["y1"] for c in row),
    )


def reconstruct(page: Any) -> str:
    rows = group_rows(page_chars(page))
    arabic = page_is_arabic(rows)
    return "\n".join(t for t in (row_text(r, arabic) for r in rows) if t)
