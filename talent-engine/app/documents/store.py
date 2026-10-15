"""Content-addressed file store: files live on a volume under their sha256, never under a name."""

from __future__ import annotations

import hashlib
from pathlib import Path


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
