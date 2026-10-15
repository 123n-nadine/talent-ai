"""Name redaction from the applicant's own name (sent as a hint, used once, never stored)."""

from __future__ import annotations

import re

PARTICLES = {
    "بن",
    "ابن",
    "بنت",
    "آل",
    "ال",
    "أبو",
    "ابو",
    "al",
    "bin",
    "ibn",
    "bint",
    "abu",
    "el",
    "the",
}
VARIANTS = {
    "ا": "[اأإآ]",
    "أ": "[اأإآ]",
    "إ": "[اأإآ]",
    "آ": "[اأإآ]",
    "ه": "[هة]",
    "ة": "[هة]",
    "ي": "[يى]",
    "ى": "[يى]",
    "و": "[وؤ]",
    "ؤ": "[وؤ]",
}
DIAC = r"[ً-ْـ]*"
B0 = r"(?<![\w؀-ۿ])"
B1 = r"(?![\w؀-ۿ])"


def _token_pattern(token: str) -> str:
    parts = []
    for ch in token:
        if "؀" <= ch <= "ۿ":
            parts.append(VARIANTS.get(ch, re.escape(ch)) + DIAC)
        else:
            parts.append(re.escape(ch))
    core = "".join(parts)
    if token.startswith("ال") and len(token) > 4:  # العتيبي also matches عتيبي
        return f"(?:ال{DIAC})?" + "".join(parts[2:])
    return core


def name_regex(hint: str | None) -> re.Pattern[str] | None:
    if not hint:
        return None
    raw = [t for t in re.split(r"[\s,،\-–/]+", hint.strip()) if t]
    tokens: list[str] = []
    for t in raw:
        if len(t) >= 3 and t.lower() not in PARTICLES:
            tokens.append(t)
    for i in range(len(raw) - 1):  # "Al-Otaibi", "بن سالم" as compounds
        if raw[i].lower() in PARTICLES and len(raw[i + 1]) >= 3:
            tokens.append(raw[i] + r"[\s\-]*" + raw[i + 1])
    if not tokens:
        return None
    alts = sorted({_token_pattern(t) if "[" not in t else t for t in tokens}, key=len, reverse=True)
    return re.compile(B0 + "(?:" + "|".join(alts) + ")" + B1, re.I)
