"""Stage 3: text extraction. Text PDF -> PyMuPDF, DOCX -> python-docx, DOC/RTF -> LibreOffice,
scanned PDF or image -> OCR provider. Any failure returns status 'unreadable' with a reason;
the screening then continues from the form answers (decision 14)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.documents.pdftext import reconstruct
from app.ocr.base import OCRProvider, OCRUnavailable

LETTERS = re.compile(r"[\w؀-ۿ]", re.UNICODE)


@dataclass
class Extraction:
    status: str  # ready | unreadable
    text: str = ""
    method: str = ""
    pages: int = 0
    chars: int = 0
    ocr_confidence: float | None = None
    error: str | None = None


def _chars(text: str) -> int:
    return len(LETTERS.findall(text))


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def _ocr_images(
    paths: list[Path], ocr: OCRProvider | None, provider_name: str
) -> tuple[str, float, str | None]:
    if ocr is None:
        raise OCRUnavailable("no OCR provider configured (ocr_provider = none)")
    texts: list[str] = []
    confs: list[float] = []
    for p in paths:
        pages = ocr.extract(str(p))
        for pg in pages:
            texts.append(pg.text)
            confs.append(pg.confidence)
    conf = round(sum(confs) / len(confs), 4) if confs else 0.0
    return "\n\n".join(texts), conf, None


def extract_pdf(
    path: Path, ocr: OCRProvider | None, settings: Settings, provider_name: str
) -> Extraction:
    import pymupdf

    try:
        doc = pymupdf.open(path)
    except Exception as e:  # noqa: BLE001
        return Extraction("unreadable", error=f"corrupt PDF: {type(e).__name__}: {e}")
    with doc:
        if doc.needs_pass:
            return Extraction(
                "unreadable", error="encrypted PDF (password protected)", pages=doc.page_count
            )
        if doc.page_count == 0:
            return Extraction("unreadable", error="PDF has no pages")
        try:
            page_texts = []
            for i in range(doc.page_count):
                page = doc.load_page(i)
                try:
                    page_texts.append(reconstruct(page))
                except Exception:  # noqa: BLE001 - fall back to plain extraction
                    page_texts.append(page.get_text("text"))
        except Exception as e:  # noqa: BLE001
            return Extraction("unreadable", error=f"corrupt PDF content: {type(e).__name__}: {e}")
        text = _clean("\n\n".join(page_texts))
        if _chars(text) >= settings.pdf_min_text_chars:
            return Extraction(
                "ready", text=text, method="pdf_text", pages=doc.page_count, chars=_chars(text)
            )
        # no usable text layer -> scanned -> OCR each rendered page
        with tempfile.TemporaryDirectory(prefix="talentai-ocr-") as tmp:
            images: list[Path] = []
            try:
                for i in range(doc.page_count):
                    pix = doc.load_page(i).get_pixmap(dpi=settings.ocr_render_dpi)
                    out = Path(tmp) / f"page-{i + 1}.png"
                    pix.save(out)
                    images.append(out)
                ocr_text, conf, _ = _ocr_images(images, ocr, provider_name)
            except OCRUnavailable as e:
                return Extraction(
                    "unreadable",
                    error=f"scanned PDF but OCR is unavailable: {e}",
                    pages=doc.page_count,
                )
            except Exception as e:  # noqa: BLE001
                return Extraction(
                    "unreadable", error=f"OCR failed: {type(e).__name__}: {e}", pages=doc.page_count
                )
        ocr_text = _clean(ocr_text)
        if not _chars(ocr_text):
            return Extraction(
                "unreadable",
                error="OCR produced no text",
                pages=doc.page_count,
                method=f"ocr:{provider_name}",
                ocr_confidence=conf,
            )
        ocr_text = _clean(ocr_text)
        return Extraction(
            "ready",
            text=ocr_text,
            method=f"ocr:{provider_name}",
            pages=doc.page_count,
            chars=_chars(ocr_text),
            ocr_confidence=conf,
        )


def extract_docx(path: Path) -> Extraction:
    import docx

    try:
        d = docx.Document(str(path))
    except Exception as e:  # noqa: BLE001
        return Extraction("unreadable", error=f"corrupt DOCX: {type(e).__name__}: {e}")
    parts = [p.text for p in d.paragraphs]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    text = _clean("\n".join(parts))
    if not _chars(text):
        return Extraction("unreadable", error="DOCX contains no text", method="docx")
    return Extraction("ready", text=text, method="docx", pages=1, chars=_chars(text))


def convert_with_libreoffice(path: Path, settings: Settings, outdir: Path) -> Path:
    exe = shutil.which(settings.libreoffice_bin)
    if not exe:
        raise RuntimeError("LibreOffice (soffice) is not installed")
    profile = outdir / "lo-profile"
    cmd = [
        exe,
        "--headless",
        "--norestore",
        "--nologo",
        f"-env:UserInstallation=file://{profile}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(outdir),
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=settings.libreoffice_timeout_s)
    pdf = outdir / (path.stem + ".pdf")
    if not pdf.exists():
        raise RuntimeError("LibreOffice produced no PDF")
    return pdf


def extract_image(path: Path, ocr: OCRProvider | None, provider_name: str) -> Extraction:
    try:
        with tempfile.TemporaryDirectory(prefix="talentai-img-") as tmp:
            # stored files have no extension; OCR engines want a real image suffix
            head = path.read_bytes()[:8]
            suffix = ".png" if head.startswith(b"\x89PNG") else ".jpg"
            img = Path(tmp) / f"scan{suffix}"
            shutil.copyfile(path, img)
            text, conf, _ = _ocr_images([img], ocr, provider_name)
    except OCRUnavailable as e:
        return Extraction("unreadable", error=f"image CV but OCR is unavailable: {e}", pages=1)
    except Exception as e:  # noqa: BLE001
        return Extraction("unreadable", error=f"OCR failed: {type(e).__name__}: {e}", pages=1)
    text = _clean(text)
    if not _chars(text):
        return Extraction(
            "unreadable",
            error="OCR produced no text",
            pages=1,
            method=f"ocr:{provider_name}",
            ocr_confidence=conf,
        )
    text = _clean(text)
    return Extraction(
        "ready",
        text=text,
        method=f"ocr:{provider_name}",
        pages=1,
        chars=_chars(text),
        ocr_confidence=conf,
    )


def extract(
    path: Path, kind: str, ocr: OCRProvider | None, settings: Settings, provider_name: str = "none"
) -> Extraction:
    if kind == "pdf":
        return extract_pdf(path, ocr, settings, provider_name)
    if kind == "docx":
        return extract_docx(path)
    if kind in ("doc", "rtf"):
        with tempfile.TemporaryDirectory(prefix="talentai-lo-") as tmp:
            try:
                pdf = convert_with_libreoffice(path, settings, Path(tmp))
            except Exception as e:  # noqa: BLE001
                return Extraction("unreadable", error=f"{kind.upper()} conversion failed: {e}")
            res = extract_pdf(pdf, ocr, settings, provider_name)
            if res.status == "ready":
                res.method = f"libreoffice+{res.method}"
            return res
    if kind == "image":
        return extract_image(path, ocr, provider_name)
    return Extraction("unreadable", error=f"unsupported file type '{kind}'")
