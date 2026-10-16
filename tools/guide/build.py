"""Build the guide in Egyptian Arabic: docs/guide/talent-ai-full-guide.pdf (Chrome, A4, RTL) and
talent-ai-full-guide.docx (same content), docs/guide/COVERAGE.md (every inventory item with its
page, screenshot and test), and the page checks (images inside the page, no overlapping text).

    tools/.venv/bin/python tools/guide/facts.py        # real numbers from the clean demo
    tools/.venv/bin/python tools/guide/shots.py        # screenshots of the clean demo
    tools/.venv/bin/python tools/guide/build.py        # this file
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ch_appendix  # noqa: E402
import ch_cases  # noqa: E402
import ch_intro  # noqa: E402
import ch_journey  # noqa: E402
import ch_rest  # noqa: E402
import ch_score  # noqa: E402
import ch_stages  # noqa: E402
import render_docx  # noqa: E402
import render_html  # noqa: E402
from inv import BY_ID, ITEMS  # noqa: E402
from lint_ar import lint_text  # noqa: E402
from model import Chapter, Diagram, Img, Page, Tech, iter_text  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GUIDE = os.path.join(ROOT, "docs", "guide")
PDF = os.path.join(GUIDE, "talent-ai-full-guide.pdf")
DOCX = os.path.join(GUIDE, "talent-ai-full-guide.docx")
CHECK = os.path.join(ROOT, "docs", "test-run", "guide_check.json")
CODE_RE = re.compile(r"\b([A-Z]{2}-\d{3})\b")
COVER = {"title": "دليل Talent AI الكامل", "sub": "الفرز والترتيب الذكي للمتقدمين جوه Frappe HR — بالعامية المصرية",
         "meta": "النسخة المحلية للتجربة · بيانات وهمية بالكامل · كل الأرقام من الاختبارات الحقيقية"}


def build_chapters(F: dict) -> tuple[list[Chapter], dict]:
    chs = [Chapter("toc", "المحتويات")]
    chs += [ch_intro.summary(F), ch_intro.manager(F), ch_intro.big_picture(F)]
    chs += ch_intro.roles(F)
    chs += [ch_journey.journey(F), ch_stages.stages(F), ch_score.score(F), ch_cases.cases(F)]
    chs += [ch_rest.privacy(F), ch_rest.results(F), ch_rest.faq(F), ch_rest.remaining(F), ch_rest.how_to_run(F), ch_rest.glossary(F)]
    claimed: dict[str, str] = {}
    dups, unknown = [], []
    for ch in chs:
        for pg in ch.pages:
            for iid in pg.ids:
                if iid not in BY_ID:
                    unknown.append(iid)
                elif iid in claimed:
                    dups.append(iid)
                else:
                    claimed[iid] = pg.id
            # every claimed item has its code printed on its page (searchable in the PDF)
            printed = {m for b in pg.blocks if isinstance(b, Tech) for ln in b.lines for m in CODE_RE.findall(ln)}
            missing = [iid for iid in pg.ids if iid in BY_ID and BY_ID[iid]["code"] not in printed]
            if missing:
                pg.blocks.append(Tech([f"{BY_ID[i]['code']} {BY_ID[i]['name']}" for i in missing]))
    for ch in chs:  # an id claimed twice stays on its first page only; no empty technical box
        for pg in ch.pages:
            pg.ids = [i for i in pg.ids if claimed.get(i) == pg.id]
            pg.blocks = [b for b in pg.blocks if not (isinstance(b, Tech) and not b.lines)]
    chs.append(ch_appendix.appendix(set(claimed)))
    chs.append(Chapter("index", "الفهرس"))
    return chs, {"duplicates": sorted(set(dups)), "unknown": sorted(set(unknown)), "claimed": len(claimed)}


def lint(chs: list[Chapter]) -> list[str]:
    out = []
    for where, text in iter_text(chs):
        for e in lint_text(text):
            out.append(f"{where}: {e} — {text[:90]}")
    return out


def fit_images(chs: list[Chapter], max_ratio: float = 0.95) -> int:
    """A screenshot much taller than wide would print too small: keep its top part (a copy in
    images/fit/, the original stays) so the text stays readable at the page width. Pages with one
    picture are sized later by fill_width, once the room left on the page is known."""
    from PIL import Image

    n = 0
    for ch in chs:
        for pg in ch.pages:
            if sum(isinstance(b, Img) for b in pg.blocks) == 1:
                continue
            for b in pg.blocks:
                if not isinstance(b, Img) or b.path.startswith("images/fit/"):
                    continue
                src = os.path.join(GUIDE, b.path)
                if not os.path.exists(src):
                    continue
                with Image.open(src) as im:
                    w, h = im.size
                    if h / w <= max_ratio or b.width < 0.8:
                        continue
                    out = os.path.join(GUIDE, "images", "fit", os.path.basename(b.path))
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    im.crop((0, 0, w, int(w * max_ratio))).save(out)
                b.path = os.path.relpath(out, GUIDE)
                n += 1
    return n


def crop_to_content(src: str, out: str, pad: int = 28) -> bool:
    """Keep only the part of a screenshot that is not page background (a refusal dialog on a dark
    overlay, or a login card on an empty page)."""
    from PIL import Image, ImageChops

    im = Image.open(src).convert("RGB")
    w, h = im.size
    border = [im.getpixel((x, 0)) for x in range(0, w, 7)] + [im.getpixel((x, h - 1)) for x in range(0, w, 7)]
    border += [im.getpixel((0, y)) for y in range(0, h, 7)] + [im.getpixel((w - 1, y)) for y in range(0, h, 7)]
    bg = max(set(border), key=border.count)
    mask = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L").point(lambda v: 255 if v > 28 else 0)
    box = mask.getbbox()
    if not box or (box[2] - box[0]) * (box[3] - box[1]) > 0.6 * w * h:
        return False
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad), min(h, box[3] + pad))).save(out)
    return True


CARD_SHOTS = {"images/steps/C_login.png": 0.6}  # one small card in the middle of an empty page


def crop_refusals(chs: list[Chapter]) -> int:
    n = 0
    for ch in chs:
        for pg in ch.pages:
            for b in pg.blocks:
                refusal = isinstance(b, Img) and b.path.startswith("images/roles/") and "الرسالة اللي بتظهر" in b.caption
                if refusal or (isinstance(b, Img) and b.path in CARD_SHOTS):
                    out = os.path.join(GUIDE, "images", "fit", ("refusal_" if refusal else "card_") + os.path.basename(b.path))
                    width = 0.75 if refusal else CARD_SHOTS[b.path]
                    if crop_to_content(os.path.join(GUIDE, b.path), out):
                        b.path = os.path.relpath(out, GUIDE)
                        b.width = width
                        n += 1
    return n


def fit_pages(chs: list[Chapter]) -> int:
    from layout import fit_page

    n = 0
    for ch in chs:
        for j, pg in enumerate(ch.pages):
            if fit_page(pg, first_of_chapter=(j == 0), intro=bool(ch.intro)) is not None:
                n += 1
    return n


def quiet_row(gray, y0: int, span: float = 0.12) -> int:
    """The calmest pixel row at or just above y0 (the gap between two lines of the screen), so a
    cut never goes through text."""
    from PIL import ImageStat

    best: list[tuple[float, int]] = []
    for y in range(y0, max(1, int(y0 * (1 - span))), -1):
        best.append((ImageStat.Stat(gray.crop((0, y, gray.width, y + 1))).stddev[0], y))
    if not best:
        return y0
    low = min(v for v, _ in best)
    return max(y for v, y in best if v <= low * 1.1 + 0.5)


def fill_width(chs: list[Chapter], min_keep: float = 0.75) -> int:
    """A picture taller than the room left on its page would print narrow and too small to read:
    keep its top part, cut at a calm row, so it fills the text width (a copy in images/fit/). A
    picture that keeps three quarters or more stays whole; `top` forces the part a page explains."""
    from PIL import Image

    from render_docx import TEXT_W_CM

    n = 0
    for ch in chs:
        for pg in ch.pages:
            imgs = [b for b in pg.blocks if isinstance(b, Img)]
            if len(imgs) != 1 or not imgs[0].crop:
                continue
            b = imgs[0]
            with Image.open(os.path.join(GUIDE, b.path)) as im:
                im.load()
                w, h = im.size
                room = int(w * b.max_h_cm / (TEXT_W_CM * b.width))  # the height that fills the width
                keep = int(h * b.top) if b.top else h
                if room < keep * min_keep:
                    keep = room
                if keep >= h:
                    continue
                cut = quiet_row(im.convert("L"), keep)
                out = os.path.join(GUIDE, "images", "fit", os.path.basename(b.path))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                im.crop((0, 0, w, cut)).save(out)
            b.path = os.path.relpath(out, GUIDE)
            n += 1
    return n


def check_images(chs: list[Chapter]) -> list[str]:
    miss = []
    for ch in chs:
        for pg in ch.pages:
            for b in pg.blocks:
                p = b.path if isinstance(b, Img) else (b.png if isinstance(b, Diagram) else None)
                if p and not os.path.exists(os.path.join(GUIDE, p)):
                    miss.append(f"{pg.id}: {p}")
    return miss


def headings(chs: list[Chapter]) -> list[tuple[str, int]]:
    out = [("cover", 1)]
    for ch in chs:
        out.append((ch.id, 1))
        if ch.id in ("toc", "index"):
            continue
        out += [(pg.id, 2) for pg in ch.pages if pg.title]
    return out


async def print_pdf(html: str, out: str) -> None:
    from playwright.async_api import async_playwright

    tmp = os.path.join(GUIDE, "_guide.html")
    open(tmp, "w", encoding="utf-8").write(html)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page()
        await pg.goto("file://" + tmp)
        await pg.wait_for_load_state("networkidle")
        await pg.evaluate("document.fonts.ready")
        await pg.pdf(path=out, format="A4", print_background=True, outline=True, tagged=True, display_header_footer=True,
                     header_template="<span></span>",
                     footer_template='<div style="width:100%;text-align:center;font-size:9px;color:#56627c;font-family:sans-serif"><span class="pageNumber"></span></div>',
                     margin={"top": "16mm", "bottom": "18mm", "left": "17mm", "right": "17mm"})
        await b.close()
    os.remove(tmp)


def pdf_pages(path: str, chs: list[Chapter]) -> tuple[dict[str, int], dict[str, int], int]:
    import pymupdf

    doc = pymupdf.open(path)
    toc = doc.get_toc()
    hs = headings(chs)
    if len(toc) != len(hs):
        raise RuntimeError(f"outline has {len(toc)} entries, expected {len(hs)}")
    pages = {hid: p for (hid, _), (_lvl, _t, p) in zip(hs, toc)}
    # the anchors the contents links to are exact; the outline is sometimes one page early when a
    # heading starts a new paper page
    for name, dest in doc.resolve_names().items():
        if name in pages and isinstance(dest, dict) and dest.get("page", -1) >= 0:
            pages[name] = dest["page"] + 1
    codes: dict[str, int] = {}
    for i, page in enumerate(doc, 1):
        for c in CODE_RE.findall(page.get_text()):
            codes.setdefault(c, i)
    return pages, codes, len(doc)


def index_entries(chs: list[Chapter], pages: dict[str, int]) -> tuple[list[tuple[str, list[int]]], list[tuple[str, list[str]]]]:
    terms: dict[str, list[str]] = {}
    for ch in chs:
        for pg in ch.pages:
            for t in pg.terms:
                terms.setdefault(t, []).append(pg.id)
            if ch.id == "journey" and pg.title:  # every screen of the journey is in the index too
                terms.setdefault(re.sub(r"^.*? — ", "", pg.title), []).append(pg.id)
    terms = {t: list(dict.fromkeys(pids)) for t, pids in terms.items()}  # a title that is also a term: one page, once
    order = sorted(terms, key=lambda t: re.sub(r"^ال", "", t))
    html_entries = [(t, sorted({pages.get(pid, 0) for pid in terms[t]})) for t in order]
    docx_entries = [(t, terms[t]) for t in order]
    return html_entries, docx_entries


def page_checks(path: str) -> dict:
    """Every image inside the page; no two text blocks overlapping; nothing outside the margins."""
    import pymupdf

    doc = pymupdf.open(path)
    problems = []
    # every page of the chapters starts with its own title: a page that starts with something else
    # holds the tail of the previous page (the contents before and the appendix and index after
    # run on by design)
    big = [(i, sp["text"]) for i, page in enumerate(doc, 1) for blk in page.get_text("dict")["blocks"]
           for ln in blk.get("lines", []) for sp in ln["spans"] if sp["size"] >= 17]
    body = (next((i for i, t in big if "الملخص" in t), 0), next((i for i, t in big if "ملحق" in t), 0))
    for i, page in enumerate(doc, 1):
        r = page.rect
        if body[0] <= i < body[1]:
            spans = sorted((ln["bbox"][1], max(sp["size"] for sp in ln["spans"])) for blk in page.get_text("dict")["blocks"]
                           for ln in blk.get("lines", []) if "".join(sp["text"] for sp in ln["spans"]).strip())
            if spans and spans[0][1] < 14.5:
                problems.append(f"page {i}: starts with the tail of the previous page")
        for info in page.get_image_info():
            b = pymupdf.Rect(info["bbox"])
            if b.x0 < r.x0 - 1 or b.y0 < r.y0 - 1 or b.x1 > r.x1 + 1 or b.y1 > r.y1 + 1:
                problems.append(f"page {i}: image outside the page {tuple(round(v) for v in b)}")
        # overlapping text = two separate text lines drawn over each other (line boxes, not blocks:
        # a block can span a whole table row and touch the next row without any visual overlap)
        lines = []
        for blk in page.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                # a lone diacritic (kasra, shadda) comes out as its own tiny fragment: not a line
                if len("".join(sp["text"] for sp in ln["spans"]).strip()) > 3:
                    # the core of the line box: a kasra or a shadda stretches the box into the
                    # next line without touching its letters
                    q = pymupdf.Rect(ln["bbox"])
                    lines.append((pymupdf.Rect(q.x0, q.y0 + q.height / 4, q.x1, q.y1 - q.height / 4), ln["spans"][0]["origin"][1]))
        hit = False
        for a in range(len(lines)):
            for c in range(a + 1, len(lines)):
                if abs(lines[a][1] - lines[c][1]) < 2:  # same baseline: one visual line cut in two by the text extractor
                    continue
                inter = lines[a][0] & lines[c][0]
                small = min(lines[a][0].get_area(), lines[c][0].get_area()) or 1
                if not inter.is_empty and inter.get_area() > 0.3 * small:
                    problems.append(f"page {i}: text lines overlap")
                    hit = True
                    break
            if hit:
                break
        blocks = [pymupdf.Rect(b[:4]) for b in page.get_text("blocks") if b[4].strip()]
        # nothing but the page number below the text area (a diacritic of the next page's first
        # heading can leak here when the heading starts a new page)
        for t in page.get_texttrace():
            digits = all(48 <= c[0] <= 57 for c in t["chars"])  # the page number itself
            if t["bbox"][1] > r.y1 - 62 and "NotoSans" not in t["font"] and not digits:
                problems.append(f"page {i}: a glyph painted in the footer area")
                break
        for b in blocks:
            if b.x0 < r.x0 + 20 or b.x1 > r.x1 - 20:
                problems.append(f"page {i}: text near the paper edge")
                break
    return {"pages": len(doc), "problems": problems}


def thumbnails(path: str, out_dir: str, per: int = 6) -> list[str]:
    """Contact sheets (6 pages each) for the visual check of every rendered page."""
    import pymupdf
    from PIL import Image

    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(path)
    sheets = []
    imgs = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=55)
        imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    for s in range(0, len(imgs), per):
        part = imgs[s:s + per]
        w, h = part[0].size
        sheet = Image.new("RGB", (w * 3 + 40, h * 2 + 30), "white")
        for j, im in enumerate(part):
            sheet.paste(im, (10 + (j % 3) * (w + 10), 10 + (j // 3) * (h + 10)))
        p = os.path.join(out_dir, f"sheet_{s // per + 1:02d}.png")
        sheet.save(p)
        sheets.append(p)
    return sheets


def ttf_fonts(tmp: str) -> dict[str, str]:
    from fontTools import merge
    from fontTools.ttLib import TTFont

    src = os.path.join(ROOT, "talent-engine", "console", "static", "fonts")
    out = {}
    for w, style in ((400, "Regular"), (700, "Bold")):
        parts = []
        for sub in ("arabic", "latin"):
            f = TTFont(os.path.join(src, f"ibm-plex-sans-arabic-{sub}-{w}-normal.woff2"))
            f.flavor = None
            p = os.path.join(tmp, f"{sub}-{w}.ttf")
            f.save(p)
            parts.append(p)
        merged = merge.Merger().merge(parts)
        p = os.path.join(tmp, f"IBMPlexSansArabic-{style}.ttf")
        merged.save(p)
        out[f"IBM Plex Sans Arabic:{style}"] = p
    f = TTFont(os.path.join(src, "ibm-plex-mono-latin-400-normal.woff2"))
    f.flavor = None
    p = os.path.join(tmp, "IBMPlexMono-Regular.ttf")
    f.save(p)
    out["IBM Plex Mono:Regular"] = p
    return out


def docx_to_pdf(docx: str, ttf: dict[str, str], out: str) -> None:
    """LibreOffice in our own engine container, with the guide fonts, for the page check of the Word file."""
    c = "talentai-api-1"
    subprocess.run(["docker", "exec", c, "sh", "-c", "rm -rf /tmp/gd && mkdir -p /tmp/gd/home/.fonts"], check=True)
    for p in ttf.values():
        subprocess.run(["docker", "cp", p, f"{c}:/tmp/gd/home/.fonts/"], check=True)
    subprocess.run(["docker", "cp", docx, f"{c}:/tmp/gd/guide.docx"], check=True)
    # bookmarks become named destinations, so the page of every bookmark can be read back
    pdf = 'pdf:writer_pdf_Export:{"ExportBookmarksToPDFDestination":{"type":"boolean","value":"true"}}'
    subprocess.run(["docker", "exec", c, "sh", "-c", f"cd /tmp/gd && HOME=/tmp/gd/home timeout 600 soffice -env:UserInstallation=file:///tmp/gd/home/lo --headless --convert-to '{pdf}' --outdir /tmp/gd /tmp/gd/guide.docx >/dev/null 2>&1"], check=True)
    subprocess.run(["docker", "cp", f"{c}:/tmp/gd/guide.pdf", out], check=True)


def bookmark_pages(pdf: str) -> dict[str, int]:
    import pymupdf

    doc = pymupdf.open(pdf)
    # LibreOffice writes "_" of a bookmark name as "5F" (our names hold only letters, digits and "_",
    # and their letters are lowercase, so "5F" can only be an underscore)
    names = {k.replace("5F", "_"): v for k, v in doc.resolve_names().items()}
    return {k: v["page"] + 1 for k, v in names.items() if k.startswith("pg_") and v.get("page", -1) >= 0}


def docx_fields_check(docx: str, now: dict[str, int], shown: dict[str, int]) -> dict:
    """Every page field of the Word file shows a number, and the number is still right after pass 2."""
    import zipfile

    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    refs = re.findall(r"PAGEREF (pg_\w+) ", xml)
    blank = len(re.findall(r'<w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>#</w:t>', xml))
    moved = sorted(k for k in set(refs) if now.get(k) != shown.get(k))
    return {"fields": len(refs), "without_number": blank, "moved_after_pass_2": moved}


async def diagram_png(svg: str, out: str) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 1000, "height": 620}, device_scale_factor=2)
        await pg.set_content(f"<html><head><style>{render_html.font_faces()} body{{margin:0;background:#fff}}</style></head><body>{svg}</body></html>")
        await pg.evaluate("document.fonts.ready")
        await pg.locator("svg").screenshot(path=out)
        await b.close()


def design_pair() -> None:
    from PIL import Image

    d = os.path.join(GUIDE, "images", "design")
    a, b = Image.open(os.path.join(d, "desk_ranking_before.png")).convert("RGB"), Image.open(os.path.join(d, "desk_ranking_after.png")).convert("RGB")
    # the first ranked rows show every change; the pair then prints at the full width
    a, b = (im.crop((0, 0, im.width, quiet_row(im.convert("L"), int(im.height * 0.55)))) for im in (a, b))
    out = Image.new("RGB", (max(a.width, b.width), a.height + b.height + 24), "white")
    out.paste(a, (0, 0))
    out.paste(b, (0, a.height + 24))
    out.save(os.path.join(d, "desk_ranking_pair.png"))


def main() -> None:
    F = json.load(open(os.path.join(GUIDE, "facts.json"), encoding="utf-8"))
    chs, claims = build_chapters(F)
    problems = lint(chs)
    if problems:
        print("\n".join(problems[:80]))
        print(f"{len(problems)} writing problem(s)")
        if "--force" not in sys.argv:
            sys.exit(1)
    asyncio.run(diagram_png(ch_intro.DIAGRAM_SVG, os.path.join(GUIDE, "images", "diagram.png")))
    design_pair()
    shutil.rmtree(os.path.join(GUIDE, "images", "fit"), ignore_errors=True)  # rebuilt below, nothing stale stays
    miss = check_images(chs)
    print("tall screenshots cut to their top part:", fit_images(chs))
    print("refusal and card screenshots cropped to the message:", crop_refusals(chs))
    print("pages fitted (picture sized to the space left):", fit_pages(chs))
    print("pictures cut to fill the text width:", fill_width(chs))
    if miss:
        print("missing images:", miss)
        sys.exit(1)
    # pass 1: page numbers of every heading and every item code; pass 2 prints them
    asyncio.run(print_pdf(render_html.render(chs, {}, [], COVER), PDF))
    pages, codes, n1 = pdf_pages(PDF, chs)
    html_idx, docx_idx = index_entries(chs, pages)
    for _ in range(3):
        asyncio.run(print_pdf(render_html.render(chs, pages, html_idx, COVER), PDF))
        pages2, codes, n = pdf_pages(PDF, chs)
        if pages2 == pages:
            break
        pages = pages2
        html_idx, docx_idx = index_entries(chs, pages)
    checks = {"pdf": page_checks(PDF), "claims": claims, "pages_stable": pages2 == pages}
    tmp = tempfile.mkdtemp()
    ttf = ttf_fonts(tmp)
    if "--no-docx" not in sys.argv:
        # pass 1 finds the page of every bookmark; pass 2 writes those pages as the fields' shown value
        render_docx.render(chs, docx_idx, COVER, DOCX, ttf)
        wpdf = os.path.join(tmp, "docx.pdf")
        docx_to_pdf(DOCX, ttf, wpdf)
        wpages = bookmark_pages(wpdf)
        render_docx.render(chs, docx_idx, COVER, DOCX, ttf, wpages)
        docx_to_pdf(DOCX, ttf, wpdf)
        checks["docx_fields"] = docx_fields_check(DOCX, bookmark_pages(wpdf), wpages)
        checks["docx_as_pdf"] = page_checks(wpdf)
        scratch = os.environ.get("TAI_SCRATCH", tmp)
        checks["sheets_docx"] = thumbnails(wpdf, os.path.join(scratch, "sheets_docx"))
        shutil.copy(wpdf, os.path.join(scratch, "docx_as_pdf.pdf"))
    scratch = os.environ.get("TAI_SCRATCH", tmp)
    checks["sheets_pdf"] = thumbnails(PDF, os.path.join(scratch, "sheets_pdf"))
    import coverage  # noqa: E402  (writes COVERAGE.md from the same build)

    cov = coverage.write(chs, codes, F)
    checks["coverage"] = cov
    os.makedirs(os.path.dirname(CHECK), exist_ok=True)
    json.dump(checks, open(CHECK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"pdf_pages": checks["pdf"]["pages"], "pdf_problems": len(checks["pdf"]["problems"]),
                      "docx_pages": checks.get("docx_as_pdf", {}).get("pages"), "docx_problems": len(checks.get("docx_as_pdf", {}).get("problems", [])),
                      "docx_fields": checks.get("docx_fields"),
                      "items": cov["items"], "items_complete": cov["complete"], "claims": claims}, ensure_ascii=False))


if __name__ == "__main__":
    main()
