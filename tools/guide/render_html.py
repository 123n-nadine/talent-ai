"""HTML of the guide (A4, RTL, IBM Plex Sans Arabic), printed to PDF by Chrome (Playwright page.pdf).

Page numbers come from a first print: the PDF outline gives the page of every heading, and the
inventory ids printed in the technical boxes give the page of every item. The second print
fills the table of contents and the index with those numbers."""

from __future__ import annotations

import html
import os
import re

from model import Bullets, Chapter, Code, Diagram, EnLine, Field, H3, Img, Note, P, Page, Rule, Table, Tech

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GUIDE = os.path.join(ROOT, "docs", "guide")
FONTS = os.path.join(ROOT, "talent-engine", "console", "static", "fonts")

LATIN_RUN = re.compile(r"(?<![&#\w])[A-Za-z0-9](?:[A-Za-z0-9_.:/@%+\-{}<>|=*]*[A-Za-z0-9%}>])?(?:\s+[A-Za-z{<](?:[A-Za-z0-9_.:/@%+\-{}<>|=*]*[A-Za-z0-9%}>])?)*")


def esc(s: str) -> str:
    return html.escape(s or "", quote=False)


def mix(s: str) -> str:
    """Escape, isolate Latin runs (so numbers and English keep their order in RTL), keep «» quotes."""
    out = []
    pos = 0
    for m in LATIN_RUN.finditer(s or ""):
        out.append(esc(s[pos:m.start()]))
        out.append(f'<bdi dir="ltr">{esc(m.group(0))}</bdi>')
        pos = m.end()
    out.append(esc((s or "")[pos:]))
    return "".join(out).replace("\n", "<br>")


def font_faces() -> str:
    faces = []
    for f in sorted(os.listdir(FONTS)):
        if not f.endswith(".woff2"):
            continue
        fam = "IBM Plex Mono" if "mono" in f else "IBM Plex Sans Arabic"
        weight = re.search(r"-(\d00)-", f).group(1)
        rng = ("U+0600-06FF, U+0750-077F, U+0870-089F, U+08A0-08FF, U+200C-200E, U+2010-2011, U+204F, U+2E41, U+FB50-FDFF, U+FE70-FE74, U+FE76-FEFC"
               if "-arabic-" in f and "latin" not in f.split("arabic-")[-1] else "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
        faces.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};src:url('file://{os.path.join(FONTS, f)}') format('woff2');unicode-range:{rng}}}")
    return "\n".join(faces)


CSS = """
@page{size:A4;margin:16mm 17mm 18mm 17mm}
:root{--text:#1f2b47;--muted:#56627c;--blue:#1e4db5;--blue-soft:#e9effc;--grey:#f1f3f7;--border:#d9dfeb;--green:#166c3c;--amber:#8a5300;--red:#b42525}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:'IBM Plex Sans Arabic',sans-serif;color:var(--text);font-size:11.5pt;line-height:1.65;direction:rtl;-webkit-print-color-adjust:exact;print-color-adjust:exact}
bdi{unicode-bidi:isolate}
h1{font-size:24pt;font-weight:700;color:var(--blue);margin:0 0 6mm;line-height:1.3}
section.chapter{break-before:page;padding-top:4mm}
h1 .num{display:inline-block;background:var(--blue);color:#fff;border-radius:8px;padding:0 10px;margin-inline-end:8px;font-size:18pt}
h2{font-size:16pt;font-weight:700;margin:0 0 4mm;line-height:1.35;border-bottom:2px solid var(--blue-soft);padding-bottom:2mm}
h3{font-size:12.5pt;font-weight:700;margin:4mm 0 1.5mm;color:var(--blue)}
h2,h3{break-after:avoid}
table thead{display:table-header-group}
section.page{break-before:page;padding-top:4mm}
section.page.nobreak{break-before:auto;margin-top:8mm}
.chapter-intro{font-size:12.5pt;color:var(--muted)}
p{margin:0 0 2.2mm}
ul,ol{margin:0 0 2.5mm;padding-inline-start:7mm}
li{margin:0 0 1mm}
figure{margin:2mm 0 3mm;break-inside:avoid;text-align:center}
figure img{max-width:100%;border:1px solid var(--border);border-radius:6px;object-fit:contain}
figcaption{font-size:10pt;color:var(--muted);margin-top:1.5mm}
pre.code{direction:ltr;text-align:left;unicode-bidi:isolate;font-family:'IBM Plex Mono','IBM Plex Sans Arabic',monospace;font-size:9.5pt;line-height:1.5;background:#0f1a33;color:#e7eeff;border-radius:6px;padding:3mm 4mm;white-space:pre-wrap;word-break:break-word;margin:1mm 0 3mm;break-inside:avoid}
.tech{background:var(--grey);border:1px solid var(--border);border-radius:6px;padding:2.5mm 4mm;margin:2mm 0 3mm;break-inside:avoid}
.tech .th{font-weight:700;color:var(--muted);font-size:10pt;margin-bottom:1mm}
.tech .tl{direction:ltr;text-align:left;unicode-bidi:isolate;font-family:'IBM Plex Mono','IBM Plex Sans Arabic',monospace;font-size:9pt;line-height:1.45;color:#2c3a58;word-break:break-word}
.tech .tl .id{color:var(--blue);font-weight:600}
.field{margin:0 0 1.5mm}
.field b{color:var(--blue)}
.rule{background:var(--blue);color:#fff;border-radius:10px;padding:5mm 6mm;font-size:15pt;font-weight:700;text-align:center;margin:4mm 0;line-height:1.6}
.note{border-inline-start:4px solid var(--blue);background:var(--blue-soft);border-radius:0 6px 6px 0;padding:2mm 4mm;margin:2mm 0 3mm;break-inside:avoid}
.note.warn{border-color:var(--amber);background:#fff4e0}
.note.ok{border-color:var(--green);background:#e6f6ec}
.enline{direction:ltr;text-align:left;unicode-bidi:isolate;color:var(--muted);font-size:10.5pt;margin:0 0 2mm}
table{width:100%;border-collapse:collapse;margin:1mm 0 3mm;font-size:10pt;line-height:1.5}
table.small{font-size:8.6pt}
th{background:var(--blue-soft);color:var(--text);font-weight:700;text-align:start;padding:1.5mm 2mm;border:1px solid var(--border)}
td{padding:1.4mm 2mm;border:1px solid var(--border);vertical-align:top;word-break:break-word}
td.ltr{direction:ltr;text-align:left;unicode-bidi:isolate;font-family:'IBM Plex Mono','IBM Plex Sans Arabic',monospace;font-size:0.92em}
tr{break-inside:avoid}
.cover{height:255mm;display:flex;flex-direction:column;justify-content:center;text-align:center}
.cover h1{break-before:auto;font-size:34pt;margin-bottom:4mm}
.cover .sub{font-size:15pt;color:var(--muted)}
.cover .meta{margin-top:20mm;font-size:11pt;color:var(--muted)}
.toc a,.idx a{color:inherit;text-decoration:none}
.toc .row{display:flex;gap:3mm;align-items:baseline;break-inside:avoid}
.toc .row .t{flex:0 1 auto}
.toc .row .dots{flex:1;border-bottom:1px dotted #aab3c5;transform:translateY(-1mm)}
.toc .row .pg{flex:none;font-family:'IBM Plex Mono',monospace;direction:ltr}
.toc .ch{font-weight:700;margin-top:2.5mm}
.toc .pg2{padding-inline-start:6mm;font-size:10.5pt}
.idx{columns:2;column-gap:8mm;font-size:10pt}
.idx .e{break-inside:avoid;display:flex;gap:2mm;justify-content:space-between;border-bottom:1px dotted #d2d8e4}
.idx .e .p{font-family:'IBM Plex Mono',monospace;direction:ltr;white-space:nowrap}
.idx .letter{font-weight:700;color:var(--blue);margin-top:2mm;break-after:avoid}
.diagram{break-inside:avoid;margin:2mm 0}
.diagram svg{width:86%;height:auto;display:block;margin:0 auto}
"""


def block_html(b) -> str:
    if isinstance(b, P):
        return f'<p class="{b.cls}">{mix(b.text)}</p>'
    if isinstance(b, H3):
        return f"<h3>{mix(b.text)}</h3>"
    if isinstance(b, Bullets):
        tag = "ol" if b.numbered else "ul"
        return f"<{tag}>" + "".join(f"<li>{mix(i)}</li>" for i in b.items) + f"</{tag}>"
    if isinstance(b, Img):
        src = "file://" + os.path.join(GUIDE, b.path)
        return (f'<figure><img src="{src}" style="max-width:{b.width * 100:.0f}%;max-height:{b.max_h_cm}cm" alt="">'
                f"<figcaption>{mix(b.caption)}</figcaption></figure>")
    if isinstance(b, Code):
        return f'<pre class="code" dir="ltr">{esc(b.text)}</pre>'
    if isinstance(b, Tech):
        lines = []
        for ln in b.lines:
            m = re.match(r"^([A-Z]{2}-\d{3}) (.*)$", ln)
            lines.append(f'<div class="tl"><span class="id">{esc(m.group(1))}</span> {esc(m.group(2))}</div>' if m else f'<div class="tl">{esc(ln)}</div>')
        return f'<div class="tech"><div class="th">{mix(b.title)}</div>{"".join(lines)}</div>'
    if isinstance(b, Table):
        cls = ' class="small"' if b.small else ""
        cols = "".join(f'<col style="width:{w * 100:.1f}%">' for w in b.widths) if b.widths else ""
        head = "".join(f"<th>{mix(h)}</th>" for h in b.head)
        rows = []
        for r in b.rows:
            cells = []
            for j, c in enumerate(r):
                if j in b.ltr_cols:
                    cells.append(f'<td class="ltr" dir="ltr">{esc(c)}</td>')
                else:
                    cells.append(f"<td>{mix(c)}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        return f"<table{cls}><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    if isinstance(b, Rule):
        return f'<div class="rule">{mix(b.text)}</div>'
    if isinstance(b, Note):
        return f'<div class="note {b.kind}">{mix(b.text)}</div>'
    if isinstance(b, EnLine):
        return f'<div class="enline" dir="ltr">{esc(b.text)}</div>'
    if isinstance(b, Field):
        return f'<div class="field"><b>{mix(b.label)}:</b> {mix(b.text)}</div>'
    if isinstance(b, Diagram):
        return f'<div class="diagram">{b.svg}<figcaption style="text-align:center">{mix(b.caption)}</figcaption></div>'
    raise TypeError(type(b))


def toc_html(chapters: list[Chapter], pages: dict[str, int]) -> str:
    rows = []
    for i, ch in enumerate(chapters, 1):
        if ch.id in ("cover", "toc"):
            continue
        pg = pages.get(ch.id, 0)
        rows.append(f'<div class="row ch"><a class="t" href="#{ch.id}">{mix(ch.title)}</a><span class="dots"></span><span class="pg">{pg or "00"}</span></div>')
        for p in ch.pages:
            if p.title and not p.id.endswith("-intro"):
                rows.append(f'<div class="row pg2"><a class="t" href="#{p.id}">{mix(p.title)}</a><span class="dots"></span><span class="pg">{pages.get(p.id, 0) or "00"}</span></div>')
    return '<div class="toc">' + "".join(rows) + "</div>"


def index_html(entries: list[tuple[str, list[int]]]) -> str:
    out = []
    last = ""
    for term, pgs in entries:
        letter = re.sub(r"^ال", "", term)[:1]
        if letter != last:
            out.append(f'<div class="letter">{esc(letter)}</div>')
            last = letter
        out.append(f'<div class="e"><span>{mix(term)}</span><span class="p">{", ".join(str(p) for p in pgs) or "—"}</span></div>')
    return '<div class="idx">' + "".join(out) + "</div>"


def render(chapters: list[Chapter], pages: dict[str, int], index: list[tuple[str, list[int]]], cover: dict) -> str:
    body = [f"""<div class="cover"><h1>{mix(cover['title'])}</h1><div class="sub">{mix(cover['sub'])}</div>
      <div class="meta">{mix(cover['meta'])}</div></div>"""]
    for i, ch in enumerate(chapters, 1):
        if ch.id == "toc":
            body.append(f'<section class="chapter"><h1 id="toc">{mix(ch.title)}</h1>' + toc_html(chapters, pages) + "</section>")
            continue
        if ch.id == "index":
            body.append(f'<section class="chapter"><h1 id="index">{mix(ch.title)}</h1>' + index_html(index) + "</section>")
            continue
        num = f'<span class="num">{ch.title.split(" ")[0]}</span>' if re.match(r"^\d+", ch.title) else ""
        title = re.sub(r"^\d+\s*[—-]?\s*", "", ch.title) if num else ch.title
        body.append(f'<section class="chapter"><h1 id="{ch.id}">{num}{mix(title)}</h1>')
        if ch.intro:
            body.append(f'<p class="chapter-intro">{mix(ch.intro)}</p>')
        for j, pg in enumerate(ch.pages):
            cls = "page" if (pg.break_before and j > 0) else "page nobreak"
            inner = "".join(block_html(b) for b in pg.blocks)
            body.append(f'<section class="{cls}" id="{pg.id}">' + (f"<h2>{mix(pg.title)}</h2>" if pg.title else "") + inner + "</section>")
        body.append("</section>")
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>{esc(cover['title'])}</title>
<style>{font_faces()}{CSS}</style></head><body>{''.join(body)}</body></html>"""
