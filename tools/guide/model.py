"""Content model of the guide: one list of blocks rendered twice (HTML → PDF with Chrome, and
Word with python-docx), so both files say exactly the same thing.

A guide is a list of Chapter objects; a chapter holds Page objects (each starts on a new paper
page); a page holds blocks. Text is Arabic with English only at the end of a line; technical
lines (DocType, fields, API) go in Tech boxes, commands and paths in Code boxes (LTR)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class P:  # one paragraph; "\n" separates lines
    text: str
    cls: str = ""


@dataclass
class H3:
    text: str


@dataclass
class Bullets:
    items: list[str]
    numbered: bool = False


@dataclass
class Img:
    path: str  # relative to docs/guide/
    caption: str
    width: float = 1.0  # share of the text width
    max_h_cm: float = 15.5
    crop: bool = True  # may keep only its top part when the page has little room (build.fill_width)
    top: float | None = None  # always keep only this top share (the part the page explains)
    fixed: bool = False  # keep max_h_cm as given (the page fitter does not shrink it)


@dataclass
class Code:  # LTR box: commands, paths, JSON
    text: str


@dataclass
class Tech:  # grey box «للفريق التقني»: one technical item per line (LTR)
    lines: list[str]
    title: str = "للفريق التقني"


@dataclass
class Table:
    head: list[str]
    rows: list[list[str]]
    ltr_cols: tuple[int, ...] = ()
    widths: tuple[float, ...] = ()
    small: bool = False


@dataclass
class Rule:  # the highlighted rule
    text: str


@dataclass
class Note:
    text: str
    kind: str = "info"  # info | warn | ok


@dataclass
class EnLine:  # an English line on its own (allowed by the writing rules)
    text: str


@dataclass
class Field:  # «who», «what you see»… label + lines
    label: str
    text: str


@dataclass
class Diagram:  # inline SVG (HTML) or a PNG (Word) of the same drawing
    svg: str
    png: str
    caption: str


@dataclass
class Page:
    id: str
    title: str
    blocks: list = field(default_factory=list)
    terms: list[str] = field(default_factory=list)  # index terms explained on this page
    ids: list[str] = field(default_factory=list)  # inventory ids explained on this page
    break_before: bool = True


@dataclass
class Chapter:
    id: str
    title: str
    pages: list[Page] = field(default_factory=list)
    intro: str = ""


TEXT_BLOCKS = (P, Bullets, Rule, Note, Field, H3)


def iter_text(chapters: list[Chapter]):
    """(where, text) for every piece of Arabic prose (used by the writing linter)."""
    for ch in chapters:
        yield f"{ch.id}", ch.title
        if ch.intro:
            yield f"{ch.id}/intro", ch.intro
        for pg in ch.pages:
            yield f"{ch.id}/{pg.id}", pg.title
            for i, b in enumerate(pg.blocks):
                w = f"{ch.id}/{pg.id}#{i}"
                if isinstance(b, (P, Rule, Note, H3)):
                    yield w, b.text
                elif isinstance(b, Field):  # rendered as one line: «label: text»
                    yield w, f"{b.label}: {b.text}"
                elif isinstance(b, Bullets):
                    for it in b.items:
                        yield w, it
                elif isinstance(b, Img):
                    yield w + " caption", b.caption
                elif isinstance(b, Diagram):
                    yield w + " caption", b.caption
                elif isinstance(b, Table):
                    for c in b.head:
                        if c and not c.isascii():
                            yield w + " head", c
                    for r in b.rows:
                        for j, c in enumerate(r):
                            if j not in b.ltr_cols and c and not c.isascii():
                                yield w + " cell", c
