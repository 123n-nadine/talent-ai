"""Every key of .env.example is used: either a Settings field of the engine or a variable of
docker-compose.yml. Keeps the documented settings and the code in step."""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings

ROOT = Path(__file__).resolve().parent.parent


def _env_keys() -> list[str]:
    keys = []
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
        if m:
            keys.append(m.group(1))
    return keys


def test_every_env_key_is_used():
    fields = {f.upper() for f in Settings.model_fields}
    compose = set(
        re.findall(
            r"\$\{([A-Z][A-Z0-9_]*)", (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        )
    )
    shell = {"TZ"}  # read by the containers' C library, not by our code
    unused = [k for k in _env_keys() if k not in fields and k not in compose and k not in shell]
    assert not unused, f".env.example keys used nowhere: {unused}"


def test_settings_load_with_defaults_only():
    s = Settings(_env_file=None)
    assert s.max_attempts >= 1 and 0 < s.ocr_min_confidence <= 1
    assert s.ai_provider in ("local", "cloud", "fake")
