"""Page fitting: a guide page with one picture must hold the picture and all its explanation on one
paper page. The text height is estimated (A4, 11.5 pt text at line height 1.65, 9 pt code) and the
picture gets the height that is left; the same limit is used by the PDF and the Word file (the
Word text is denser, so the estimate is on the safe side there)."""

from __future__ import annotations

import math

from model import Bullets, Code, Diagram, EnLine, Field, H3, Img, Note, P, Page, Rule, Table, Tech

PAGE_MM = 263 - 6 - 12  # A4 297 mm minus the 16/18 mm margins, the section padding and a safety margin
CHAPTER_HEAD_MM = 26    # the chapter title on the first page of a chapter (and its intro line)
LINE_MM = 6.7           # 11.5 pt × 1.65
CHARS = 82              # Arabic characters on one text line (176 mm)
TECH_LINE_MM = 4.4      # 9 pt mono × 1.45 (plus the box)
TECH_CHARS = 92


def _lines(text: str, chars: int = CHARS) -> int:
    return sum(max(1, math.ceil(len(t) / chars)) for t in (text or "").split("\n"))


def text_mm(pg: Page) -> float:
    mm = 15.0 if pg.title else 0.0  # h2 + rule
    for b in pg.blocks:
        if isinstance(b, (P, Note)):
            mm += _lines(b.text) * LINE_MM + (2.5 if isinstance(b, P) else 7)
        elif isinstance(b, Field):
            mm += _lines(f"{b.label}: {b.text}") * LINE_MM + 1.5
        elif isinstance(b, Bullets):
            mm += sum(_lines(i, CHARS - 6) for i in b.items) * LINE_MM + 3
        elif isinstance(b, Tech):
            mm += 12 + sum(max(1, math.ceil(len(ln) / TECH_CHARS)) for ln in b.lines) * TECH_LINE_MM
        elif isinstance(b, Code):
            mm += 10 + _lines(b.text, TECH_CHARS) * TECH_LINE_MM
        elif isinstance(b, Rule):
            mm += 20
        elif isinstance(b, (H3, EnLine)):
            mm += 9
        elif isinstance(b, Table):
            mm += 8 + 7 * (1 + len(b.rows))
        elif isinstance(b, (Img, Diagram)):
            mm += 12  # caption and figure margins
    return mm


def fit_page(pg: Page, first_of_chapter: bool, intro: bool) -> float | None:
    """Set the picture height of a one-picture page so everything fits. Returns the height (cm)."""
    imgs = [b for b in pg.blocks if isinstance(b, Img)]
    if len(imgs) != 1:
        return None
    avail = PAGE_MM - (CHAPTER_HEAD_MM + (8 if intro else 0) if first_of_chapter else 0) - text_mm(pg)
    h_cm = max(5.0, min(imgs[0].max_h_cm, avail / 10))
    imgs[0].max_h_cm = round(h_cm, 1)
    return imgs[0].max_h_cm
