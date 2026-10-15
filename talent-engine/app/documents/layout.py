"""Helpers over an extraction layout: map evidence quotes to boxes, render page images."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from app.core.arabic import normalize
from app.documents.extract import DISPLAY_DPI

TOKEN = re.compile(r"\[[^\]]{1,20}\]")


def quote_fragments(quote: str) -> list[str]:
    """A redacted quote may contain tokens like [الاسم]; match the real text around them."""
    return [f for f in (normalize(x) for x in TOKEN.split(quote or "")) if len(f) >= 4]


def boxes_for_quote(quote: str | None, layout: dict[str, Any] | None) -> list[list[int]]:
    """Return [[line_index, box_index], ...] of the boxes that carry the quote (box_index -1 = whole line)."""
    if not quote or not layout:
        return []
    frags = quote_fragments(quote)
    if not frags:
        return []
    hits: list[list[int]] = []
    for li, line in enumerate(layout.get("lines", [])):
        lt = normalize(line.get("t"))
        if not lt:
            continue
        line_hit = any(
            f in lt
            or (len(lt) >= 8 and lt in f)
            or (len(f) >= 12 and fuzz.partial_ratio(f, lt) >= 92)
            for f in frags
        )
        if not line_hit:
            continue
        boxes = line.get("boxes") or []
        if len(boxes) <= 1:
            hits.append([li, -1])
            continue
        any_box = False
        for bi, b in enumerate(boxes):
            bt = normalize(b[5] if len(b) > 5 else "")
            if len(bt) >= 3 and any(bt in f or f in bt for f in frags):
                hits.append([li, bi])
                any_box = True
        if not any_box:
            hits.append([li, -1])
    return hits


def render_page(path: Path, kind: str, page: int) -> tuple[bytes, str]:
    """PNG of a PDF page at DISPLAY_DPI, or the original image bytes."""
    if kind == "image":
        data = path.read_bytes()
        return data, ("image/png" if data[:8].startswith(b"\x89PNG") else "image/jpeg")
    import pymupdf

    with pymupdf.open(path) as doc:
        if page < 0 or page >= doc.page_count:
            raise IndexError("page out of range")
        pix = doc.load_page(page).get_pixmap(dpi=DISPLAY_DPI)
        return pix.tobytes("png"), "image/png"


def page_data_uri(data: bytes, mime: str) -> str:
    import base64

    return f"data:{mime};base64," + base64.b64encode(data).decode()


def image_size(data: bytes) -> tuple[int, int]:
    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        return im.width, im.height
