"""Writing rules of the guide (Nadine, round 2), checked on every text line of the content:

1. never «يتم», «حيث» or «وذلك»;
2. every line starts with an Arabic word;
3. English (Latin letters) only at the end of a line, never followed by Arabic words; a line that
   is all English is allowed only as its own line (`en_line`) or inside a code box;
4. no two consecutive sentences start with the same word.

    python3 tools/guide/lint_ar.py        # lints tools/guide/content.py through the model
"""

from __future__ import annotations

import re

AR = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z]")
BANNED = re.compile(r"(?<![؀-ۿ])(?:[وف]?يتم|حيث|وذلك)(?![؀-ۿ])")
SENT_SPLIT = re.compile(r"(?<=[.!؟?:])\s+|\n")
PUNCT = "«»()[]\"'،,.:;!؟?…—–-·•/"


def first_word(s: str) -> str:
    s = s.strip().lstrip(PUNCT + " ").strip()
    w = s.split()[0] if s.split() else ""
    return w.strip(PUNCT)


def check_line(line: str) -> list[str]:
    """Problems of one line of guide text (empty list = fine)."""
    errs = []
    t = line.strip()
    if not t:
        return errs
    m = BANNED.search(t)
    if m:
        errs.append(f"banned word «{m.group(0)}»")
    fw = first_word(re.sub(r"^[\d.\-–)\s]+", "", t))
    if fw and not AR.search(fw):
        errs.append(f"line does not start with an Arabic word: «{fw}»")
    # Latin then Arabic again = English in the middle of the line
    words = re.findall(r"\S+", t)
    seen_latin = False
    for w in words:
        if LATIN.search(w):
            seen_latin = True
        elif AR.search(w) and seen_latin:
            errs.append(f"English in the middle of the line, before «{w}»")
            break
    return errs


def check_sentences(text: str) -> list[str]:
    errs = []
    prev = None
    for sent in [s for s in SENT_SPLIT.split(text) if s.strip()]:
        fw = first_word(sent)
        if fw and prev and fw == prev and AR.search(fw):
            errs.append(f"two sentences in a row start with «{fw}»")
        prev = fw
    return errs


def lint_text(text: str) -> list[str]:
    out = []
    for line in text.split("\n"):
        out += check_line(line)
    out += check_sentences(text)
    return out


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from model import iter_text  # noqa: E402

    import content  # noqa: E402

    bad = 0
    for where, text in iter_text(content.build()):
        for e in lint_text(text):
            bad += 1
            print(f"{where}: {e}\n    {text[:120]}")
    print(f"{bad} problem(s)")
    sys.exit(1 if bad else 0)
