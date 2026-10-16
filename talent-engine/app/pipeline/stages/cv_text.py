"""The CV text a screening may use (round 3 review, item 3).

A badly read OCR line (confidence under `ocr_min_confidence`) is not evidence of anything: it is
taken out of the text before the language model sees it and before any quote is checked, so it
can never carry a judgement. The line keeps its place (a marker stands in for it) so the layout
boxes, the redaction view and the text stay aligned line by line."""

from __future__ import annotations

from typing import Any

WEAK_MARK = "[سطر ضعيف القراءة — مستبعد من الأدلة]"


def weak_line_indices(layout: dict[str, Any] | None, min_confidence: float) -> list[int]:
    """Indices of the layout lines read with a confidence under the threshold (OCR only: a text
    layer has confidence 1)."""
    if not layout:
        return []
    out = []
    for i, ln in enumerate(layout.get("lines") or []):
        c = ln.get("c")
        if c is not None and float(c) < min_confidence:
            out.append(i)
    return out


def evidence_text(
    redacted_text: str | None, layout: dict[str, Any] | None, min_confidence: float
) -> tuple[str, list[int]]:
    """The redacted text with every weak line replaced by the marker, and the indices replaced.
    The text and the layout lines match one to one (the extractor builds the text from the same
    lines and the redaction keeps line breaks); when they do not, nothing is excluded."""
    text = redacted_text or ""
    idx = weak_line_indices(layout, min_confidence)
    if not idx:
        return text, []
    lines = text.split("\n")
    if len(lines) != len(layout.get("lines") or []):  # type: ignore[union-attr]
        return text, []
    for i in idx:
        lines[i] = WEAK_MARK
    return "\n".join(lines), idx
