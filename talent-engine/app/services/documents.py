"""CV documents: store, extract, redact (at upload time, so the name hint is used once and dropped)."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.ids import new_id
from app.core.timeutil import iso, utcnow
from app.documents.detect import ALLOWED_KINDS, sniff
from app.documents.extract import Extraction, extract
from app.documents.store import FileStore, release_files
from app.ocr.base import OCRProvider, OCRUnavailable
from app.ocr.registry import get_ocr
from app.redaction.engine import RedactionResult, redact
from app.services import audit
from app.services.candidates import data_hash, doc_fingerprint
from app.storage.models import Candidate, Document, Tenant


class DocumentError(ValueError):
    pass


@dataclass
class Processed:
    kind: str
    mime: str
    sha256: str
    size: int
    extraction: Extraction
    redaction: RedactionResult | None


def _ocr_for(tenant: Tenant, settings: Settings) -> tuple[OCRProvider | None, str]:
    name = tenant.ocr_provider or "none"
    try:
        return get_ocr(name, settings), name
    except OCRUnavailable:
        return None, name


def validate_upload(filename: str | None, content: bytes, settings: Settings) -> tuple[str, str]:
    if not content:
        raise DocumentError("empty file")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise DocumentError(f"file larger than {settings.max_upload_mb} MB")
    kind, mime = sniff(filename, content)
    if kind not in ALLOWED_KINDS:
        raise DocumentError("unsupported file type (allowed: PDF, DOCX, DOC, RTF, JPG, PNG)")
    return kind, mime


def process(
    content: bytes,
    kind: str,
    mime: str,
    tenant: Tenant,
    settings: Settings,
    name_hint: str | None,
    path: Path | None = None,
) -> Processed:
    import hashlib

    sha = hashlib.sha256(content).hexdigest()
    ocr, ocr_name = _ocr_for(tenant, settings)
    ext = {"pdf": ".pdf", "docx": ".docx", "doc": ".doc", "rtf": ".rtf"}.get(
        kind, ".png" if mime == "image/png" else ".jpg"
    )
    if path is None:
        with tempfile.TemporaryDirectory(prefix="talentai-doc-") as tmp:
            p = Path(tmp) / f"upload{ext}"
            p.write_bytes(content)
            ex = extract(p, kind, ocr, settings, ocr_name)
    else:
        ex = extract(path, kind, ocr, settings, ocr_name)
    red = (
        redact(ex.text, name_hint, use_nlp=settings.redaction_nlp) if ex.status == "ready" else None
    )
    return Processed(kind, mime, sha, len(content), ex, red)


def attach_cv(
    db: Session,
    settings: Settings,
    tenant: Tenant,
    cand: Candidate,
    filename: str | None,
    content: bytes,
    name_hint: str | None,
    actor: str = "adapter",
) -> Document:
    kind, mime = validate_upload(filename, content, settings)
    store = FileStore(settings.file_store)
    sha, path = store.save(content)
    pr = process(content, kind, mime, tenant, settings, name_hint, path=path)
    preview_sha = None
    if pr.extraction.preview_pdf:
        preview_sha, _ = store.save(pr.extraction.preview_pdf)
    released: set[str | None] = set()
    for old in [d for d in cand.documents if d.kind == "cv"]:
        db.delete(old)
        released |= {old.sha256, old.preview_sha256}
    doc = Document(
        id=new_id("doc"),
        candidate_id=cand.id,
        kind="cv",
        mime=mime,
        sha256=sha,
        size_bytes=len(content),
        status=pr.extraction.status,
        text=pr.extraction.text or None,
        extraction_method=pr.extraction.method or None,
        ocr_confidence=pr.extraction.ocr_confidence,
        redacted_text=pr.redaction.text if pr.redaction else None,
        redaction_report={"counts": pr.redaction.report, "engine": pr.redaction.engine}
        if pr.redaction
        else None,
        error=pr.extraction.error,
        page_count=pr.extraction.pages,
        char_count=pr.extraction.chars,
        name_hint_used=bool(name_hint),
        processed_at=utcnow(),
        layout=pr.extraction.layout,
        preview_sha256=preview_sha,
    )
    db.add(doc)
    db.flush()
    release_files(db, settings.file_store, released)  # the new file may be the same one: kept
    db.refresh(cand)
    cand.data_hash = data_hash(
        cand.id_token, cand.facts, cand.answers, [doc_fingerprint(d) for d in cand.documents]
    )
    audit.log(
        db,
        tenant.id,
        cand.external_ref,
        "candidate.cv_attached",
        actor,
        {
            "document_id": doc.id,
            "sha256": sha,
            "kind": kind,
            "status": doc.status,
            "method": doc.extraction_method,
            "ocr_confidence": doc.ocr_confidence,
            "chars": doc.char_count,
            "pages": doc.page_count,
            "redacted": (pr.redaction.report if pr.redaction else None),
            "error": doc.error,
            "data_hash": cand.data_hash,
        },
    )
    db.flush()
    return doc


def remove_cv(
    db: Session, settings: Settings, tenant: Tenant, cand: Candidate, actor: str = "adapter"
) -> int:
    n = 0
    released: set[str | None] = set()
    for old in [d for d in cand.documents if d.kind == "cv"]:
        db.delete(old)
        released |= {old.sha256, old.preview_sha256}
        n += 1
    db.flush()
    release_files(db, settings.file_store, released)
    db.refresh(cand)
    cand.data_hash = data_hash(
        cand.id_token, cand.facts, cand.answers, [doc_fingerprint(d) for d in cand.documents]
    )
    audit.log(
        db,
        tenant.id,
        cand.external_ref,
        "candidate.cv_removed",
        actor,
        {"removed": n, "data_hash": cand.data_hash},
    )
    db.flush()
    return n


def page_source(settings: Settings, doc: Document) -> tuple[Path, str]:
    """File and kind used to render the page images of a stored CV."""
    store = FileStore(settings.file_store)
    if doc.preview_sha256:
        return store.path_for(doc.preview_sha256), "pdf"
    if (doc.mime or "").startswith("image/"):
        return store.path_for(doc.sha256), "image"
    return store.path_for(doc.sha256), "pdf"


def raw_lines_vs_redacted(raw: str | None, redacted: str | None) -> list[list[str]]:
    """Pairs of (before, after) lines for the redaction view (line breaks are preserved)."""
    a = (raw or "").split("\n")
    b = (redacted or "").split("\n")
    if len(a) != len(b):
        return []
    return [[x, y] for x, y in zip(a, b, strict=False)]


def document_out(
    doc: Document,
    include_text: bool = False,
    include_raw: bool = False,
    min_confidence: float | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": doc.id,
        "kind": doc.kind,
        "mime": doc.mime,
        "sha256": doc.sha256,
        "size_bytes": doc.size_bytes,
        "status": doc.status,
        "extraction_method": doc.extraction_method,
        "ocr_confidence": doc.ocr_confidence,
        "pages": doc.page_count,
        "chars": doc.char_count,
        "error": doc.error,
        "redaction": doc.redaction_report,
        "name_hint_used": doc.name_hint_used,
        "created_at": iso(doc.created_at),
        "processed_at": iso(doc.processed_at),
    }
    if include_text:
        out["redacted_text"] = doc.redacted_text
        out["layout"] = doc.layout
        if min_confidence is not None:
            from app.pipeline.stages.cv_text import weak_line_indices

            out["min_confidence"] = min_confidence
            out["weak_lines"] = weak_line_indices(doc.layout, min_confidence)
        out["page_images"] = (
            [f"pages/{i}" for i in range(doc.page_count or 0)]
            if doc.status == "ready" or doc.layout
            else []
        )
    if include_raw:
        out["raw_text"] = doc.text
        out["redaction_pairs"] = raw_lines_vs_redacted(doc.text, doc.redacted_text)
    return out


def inspect_out(pr: Processed, include_raw: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {
        "stored": False,
        "kind": pr.kind,
        "mime": pr.mime,
        "sha256": pr.sha256,
        "size_bytes": pr.size,
        "status": pr.extraction.status,
        "extraction_method": pr.extraction.method or None,
        "ocr_confidence": pr.extraction.ocr_confidence,
        "pages": pr.extraction.pages,
        "chars": pr.extraction.chars,
        "error": pr.extraction.error,
        "redaction": {"counts": pr.redaction.report, "engine": pr.redaction.engine}
        if pr.redaction
        else None,
        "redacted_text": pr.redaction.text if pr.redaction else None,
    }
    out["layout"] = pr.extraction.layout
    if include_raw:
        out["raw_text"] = pr.extraction.text
        out["redaction_pairs"] = raw_lines_vs_redacted(
            pr.extraction.text, pr.redaction.text if pr.redaction else None
        )
    return out


def inspect_pages(content: bytes, pr: Processed, max_pages: int = 3) -> list[str]:
    """Page images as data URIs for an uploaded (not stored) file."""
    from app.documents.layout import page_data_uri, render_page

    if pr.extraction.layout is None:
        return []
    with tempfile.TemporaryDirectory(prefix="talentai-insp-") as tmp:
        if pr.extraction.preview_pdf:
            src, kind = Path(tmp) / "preview.pdf", "pdf"
            src.write_bytes(pr.extraction.preview_pdf)
        elif pr.kind == "image":
            src, kind = Path(tmp) / "img", "image"
            src.write_bytes(content)
        else:
            src, kind = Path(tmp) / "doc.pdf", "pdf"
            src.write_bytes(content)
        out = []
        for i in range(min(len(pr.extraction.layout.get("pages", [])), max_pages)):
            try:
                data, mime = render_page(src, kind, i)
                out.append(page_data_uri(data, mime))
            except Exception:  # noqa: BLE001
                break
        return out
