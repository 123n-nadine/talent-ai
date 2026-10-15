"""Versioned prompt files in talent-engine/prompts/. The version id is stored on every result."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

PROFILE = "profile-v1"
JUDGE = "judge-v1"
DRAFT = "draft-criteria-v1"


@lru_cache
def load(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
