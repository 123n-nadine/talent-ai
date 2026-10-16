from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
from app.documents.store import FileStore
from app.services import candidates as cand_svc
from app.services import documents as doc_svc
from app.storage.models import Tenant

router = APIRouter(prefix="/v1", tags=["documents"])


def _read(file: UploadFile) -> bytes:
    return file.file.read()


@router.put("/candidates/{ref}/cv")
def attach_cv(
    ref: str,
    file: UploadFile = File(...),
    name_hint: str | None = Form(default=None),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    """Attach (or replace) the candidate's CV. Extraction and redaction run now; `name_hint`
    (the applicant's own name) is used for redaction and never stored."""
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    if not cand.consent:
        raise HTTPException(status_code=409, detail="candidate has no consent to AI processing")
    try:
        doc = doc_svc.attach_cv(
            db, settings, tenant, cand, file.filename, _read(file), name_hint, actor
        )
    except doc_svc.DocumentError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    db.commit()
    return {
        "candidate_ref": ref,
        "data_hash": cand.data_hash,
        "document": doc_svc.document_out(doc, include_text=True),
    }


def _cv_doc(db: Session, tenant: Tenant, ref: str):
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    doc = next((d for d in cand.documents if d.kind == "cv"), None)
    if doc is None:
        raise HTTPException(status_code=404, detail="candidate has no CV")
    return cand, doc


@router.get("/candidates/{ref}/cv")
def get_cv(
    ref: str,
    include_raw: bool = False,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    """Redacted text, layout (lines with boxes and confidence) and page image paths. `include_raw`
    adds the text before redaction (for the HR system and the console; never sent to an LLM).
    `weak_lines` are the OCR lines under `min_confidence`: never used as evidence."""
    _, doc = _cv_doc(db, tenant, ref)
    return {
        "candidate_ref": ref,
        "document": doc_svc.document_out(
            doc,
            include_text=True,
            include_raw=include_raw,
            min_confidence=settings.ocr_min_confidence,
        ),
    }


@router.get("/candidates/{ref}/cv/file")
def get_cv_file(
    ref: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    """The original uploaded file."""
    _, doc = _cv_doc(db, tenant, ref)
    path = FileStore(settings.file_store).path_for(doc.sha256)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return Response(
        path.read_bytes(),
        media_type=doc.mime or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="cv-{ref}"',
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/candidates/{ref}/cv/pages/{page}")
def get_cv_page(
    ref: str,
    page: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    """Page image in the same pixel space as the layout boxes."""
    from app.documents.layout import render_page

    _, doc = _cv_doc(db, tenant, ref)
    src, kind = doc_svc.page_source(settings, doc)
    if not src.exists():
        raise HTTPException(status_code=404, detail="file not found")
    try:
        data, mime = render_page(src, kind, page)
    except IndexError as e:
        raise HTTPException(status_code=404, detail="page out of range") from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=422, detail=f"page cannot be rendered: {type(e).__name__}"
        ) from e
    return Response(data, media_type=mime, headers={"Cache-Control": "private, max-age=300"})


@router.delete("/candidates/{ref}/cv")
def delete_cv(
    ref: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
    actor: str = Depends(actor_from),
):
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    n = doc_svc.remove_cv(db, settings, tenant, cand, actor)
    db.commit()
    return {"candidate_ref": ref, "removed": n, "data_hash": cand.data_hash}


@router.post("/documents/inspect")
def inspect(
    file: UploadFile = File(...),
    name_hint: str | None = Form(default=None),
    include_raw: bool = Form(default=False),
    tenant: Tenant = Depends(get_tenant),
    settings: Settings = Depends(get_settings_dep),
):
    """Extract and redact a file WITHOUT storing anything (for testing OCR and redaction)."""
    content = _read(file)
    try:
        kind, mime = doc_svc.validate_upload(file.filename, content, settings)
    except doc_svc.DocumentError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    pr = doc_svc.process(content, kind, mime, tenant, settings, name_hint)
    out = doc_svc.inspect_out(pr, include_raw=include_raw)
    out["page_images"] = doc_svc.inspect_pages(content, pr)
    return out
