from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import actor_from, get_db, get_settings_dep, get_tenant
from app.core.config import Settings
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


@router.get("/candidates/{ref}/cv")
def get_cv(ref: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    cand = cand_svc.get_candidate(db, tenant, ref)
    if cand is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    doc = next((d for d in cand.documents if d.kind == "cv"), None)
    if doc is None:
        raise HTTPException(status_code=404, detail="candidate has no CV")
    return {"candidate_ref": ref, "document": doc_svc.document_out(doc, include_text=True)}


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
    return doc_svc.inspect_out(pr, include_raw=include_raw)
