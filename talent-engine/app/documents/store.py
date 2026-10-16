"""Content-addressed file store: files live on a volume under their sha256, never under a name.

Two documents can hold the same file (the same CV uploaded twice), so a file is removed only when
no document references it any more, and only once the transaction that dropped the last
reference has committed (a rollback keeps it)."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import event, or_, select
from sqlalchemy.orm import Session

_PENDING = "talentai_files_to_delete"


class FileStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, sha256: str) -> Path:
        return self.root / sha256[:2] / sha256

    def save(self, content: bytes) -> tuple[str, Path]:
        sha = hashlib.sha256(content).hexdigest()
        p = self.path_for(sha)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(content)
        return sha, p

    def delete(self, sha256: str) -> bool:
        p = self.path_for(sha256)
        if p.exists():
            p.unlink()
            return True
        return False


def release_files(db: Session, root: str | Path, shas: Iterable[str | None]) -> int:
    """Schedule the removal of the stored files (originals and previews) that no remaining
    document references. Call it after the documents were deleted in this session."""
    from app.storage.models import Document

    wanted = {s for s in shas if s}
    if not wanted:
        return 0
    db.flush()
    used: set[str] = set()
    for sha, preview in db.execute(
        select(Document.sha256, Document.preview_sha256).where(
            or_(Document.sha256.in_(wanted), Document.preview_sha256.in_(wanted))
        )
    ):
        used.update(x for x in (sha, preview) if x)
    gone = wanted - used
    db.info.setdefault(_PENDING, set()).update((str(root), sha) for sha in gone)
    return len(gone)


@event.listens_for(Session, "after_commit")
def _delete_released(session: Session) -> None:
    for root, sha in session.info.pop(_PENDING, set()):
        FileStore(root).delete(sha)


@event.listens_for(Session, "after_rollback")
def _keep_released(session: Session) -> None:
    session.info.pop(_PENDING, None)
