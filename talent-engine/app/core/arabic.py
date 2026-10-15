"""Arabic text normalisation used for evidence matching and value comparison."""

import re
import unicodedata

_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_SPACES = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    """Lower-case, unify Arabic letter variants, Arabic-Indic digits and whitespace."""
    if text is None:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    s = s.translate(_ARABIC_INDIC)
    s = _DIACRITICS.sub("", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = _SPACES.sub(" ", s).strip().casefold()
    return s


def same(a: str | None, b: str | None) -> bool:
    return normalize(a) == normalize(b)
