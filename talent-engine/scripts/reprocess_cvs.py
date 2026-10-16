"""Re-extract and re-redact every stored CV with the current code, in place.

Round 3 review: an e-mail survived the redaction of Arabic text PDFs because the extraction had
put its dot elsewhere. After the fix every stored document is run through extraction and
redaction again; the candidate's data hash changes when the text changed, so the host system
sees the old result as stale and re-scores it («إعادة تقييم القديم والفاشل»).

Runs inside the api container (it needs the database and the file store):

    docker exec talentai-api-1 python -m scripts.reprocess_cvs            # report only
    docker exec talentai-api-1 python -m scripts.reprocess_cvs --apply    # rewrite the documents

The report lists, per document, whether the redacted text held something that looks like
personal data before and after. Nothing personal is printed: counts and references only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.timeutil import utcnow
from app.documents.detect import sniff
from app.documents.store import FileStore
from app.redaction.engine import leak_check
from app.services import audit
from app.services.candidates import data_hash, doc_fingerprint
from app.services.documents import process
from app.storage.db import make_engine, make_sessionmaker
from app.storage.models import Candidate, Document, Tenant


def recover_name_hints(old_text: str | None, old_redacted: str | None) -> list[str]:
    """The engine never stores the applicant's name, so the hint the host gave at upload time is
    gone; the pieces the earlier redaction replaced by [الاسم] are read back from the old text
    and used as hints again (lines of the raw and the redacted text match one to one)."""
    import difflib

    from app.redaction.patterns import TOKENS

    raw = (old_text or "").split("\n")
    red = (old_redacted or "").split("\n")
    if len(raw) != len(red):
        return []
    hints: list[str] = []
    for a, b in zip(raw, red, strict=False):
        if TOKENS["NAME"] not in b:
            continue
        wa, wb = a.split(), b.split()  # word by word: letters shared by the name and the token
        sm = difflib.SequenceMatcher(
            None, wa, wb, autojunk=False
        )  # would mislead a diff by character
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("replace", "delete") and any(TOKENS["NAME"] in w for w in wb[j1:j2] or [""]):
                piece = " ".join(wa[i1:i2]).strip(" :،,.-—")
                if len(piece) >= 3 and piece not in hints:
                    hints.append(piece)
    return hints


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the new text, layout and redaction")
    args = ap.parse_args()
    settings = get_settings()
    store = FileStore(settings.file_store)
    db = make_sessionmaker(make_engine(settings.database_url))()
    rows = db.execute(
        select(Document, Candidate, Tenant)
        .join(Candidate, Candidate.id == Document.candidate_id)
        .join(Tenant, Tenant.id == Candidate.tenant_id)
    ).all()
    leaked_before, leaked_after, changed, missing = [], [], [], []
    for doc, cand, tenant in rows:
        before = leak_check(doc.redacted_text)
        if before:
            leaked_before.append(cand.external_ref)
        path = store.path_for(doc.sha256)
        if not path.exists():
            missing.append(cand.external_ref)
            continue
        content = path.read_bytes()
        kind, mime = sniff(None, content)
        hints = recover_name_hints(doc.text, doc.redacted_text)
        pr = process(content, kind, mime, tenant, settings, " ".join(hints) or None, path=path)
        new_text = pr.redaction.text if pr.redaction else None
        for h in hints:  # every name piece the old redaction knew is gone from the new text too
            if pr.redaction is not None and h in pr.redaction.text:
                from app.redaction.names import name_regex

                rx = name_regex(h)
                if rx is not None:
                    pr.redaction.text = rx.sub("[الاسم]", pr.redaction.text)
                    pr.redaction.report["name"] = pr.redaction.report.get("name", 0) + 1
        new_text = pr.redaction.text if pr.redaction else None
        after = leak_check(new_text)
        if after:
            leaked_after.append(cand.external_ref)
        if (new_text or "") != (doc.redacted_text or "") or pr.extraction.text != (doc.text or ""):
            changed.append(cand.external_ref)
            if args.apply:
                doc.status = pr.extraction.status
                doc.text = pr.extraction.text or None
                doc.extraction_method = pr.extraction.method or None
                doc.ocr_confidence = pr.extraction.ocr_confidence
                doc.redacted_text = new_text
                doc.redaction_report = (
                    {"counts": pr.redaction.report, "engine": pr.redaction.engine}
                    if pr.redaction
                    else None
                )
                doc.error = pr.extraction.error
                doc.page_count = pr.extraction.pages
                doc.char_count = pr.extraction.chars
                doc.layout = pr.extraction.layout
                doc.processed_at = utcnow()
                db.flush()
                db.refresh(cand)
                cand.data_hash = data_hash(
                    cand.id_token,
                    cand.facts,
                    cand.answers,
                    [doc_fingerprint(d) for d in cand.documents],
                )
                audit.log(
                    db,
                    tenant.id,
                    cand.external_ref,
                    "candidate.cv_reprocessed",
                    "system",
                    {
                        "document_id": doc.id,
                        "leak_before": len(before),
                        "leak_after": len(after),
                        "data_hash": cand.data_hash,
                    },
                )
    if args.apply:
        db.commit()
    print(f"documents: {len(rows)}; text changed: {len(changed)}; file missing: {len(missing)}")
    print(f"leak before: {len(leaked_before)} {sorted(leaked_before)}")
    print(f"leak after:  {len(leaked_after)} {sorted(leaked_after)}")
    print("applied" if args.apply else "report only (use --apply to write)")
    return 1 if leaked_after else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    raise SystemExit(main())
