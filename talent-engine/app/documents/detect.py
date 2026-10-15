"""File kind detection by magic bytes (extension only as a fallback)."""

from __future__ import annotations

from pathlib import PurePath

ALLOWED_KINDS = {"pdf", "docx", "doc", "rtf", "image"}
MIMES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "rtf": "application/rtf",
    "jpeg": "image/jpeg",
    "png": "image/png",
}
EXT_KINDS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".rtf": "rtf",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
}


def sniff(filename: str | None, content: bytes) -> tuple[str, str]:
    """Return (kind, mime). kind is one of pdf, docx, doc, rtf, image or unknown."""
    head = content[:8]
    if head.startswith(b"%PDF"):
        return "pdf", MIMES["pdf"]
    if head.startswith(b"PK\x03\x04"):
        if b"word/" in content[:6000] or (filename or "").lower().endswith(".docx"):
            return "docx", MIMES["docx"]
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "doc", MIMES["doc"]
    if head.startswith(b"{\\rtf"):
        return "rtf", MIMES["rtf"]
    if head.startswith(b"\xff\xd8\xff"):
        return "image", MIMES["jpeg"]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image", MIMES["png"]
    ext = PurePath(filename or "").suffix.lower()
    kind = EXT_KINDS.get(ext, "unknown")
    mime = MIMES.get(kind, "image/jpeg" if kind == "image" else "application/octet-stream")
    return kind, mime
