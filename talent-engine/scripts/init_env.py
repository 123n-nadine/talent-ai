"""Create .env from .env.example with random secrets. Usage: python -m scripts.init_env [--force]"""

from __future__ import annotations

import pathlib
import re
import secrets
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECRET_KEYS = (
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "TENANT_API_KEY",
    "CALLBACK_SECRET",
    "CONSOLE_PASSWORD",
    "CONSOLE_SESSION_SECRET",
    "CONSOLE_ID_TOKEN_SECRET",
)


def main() -> int:
    target = ROOT / ".env"
    force = "--force" in sys.argv
    if target.exists() and not force:
        print(".env exists; use --force to regenerate (this rotates every secret)")
        return 1
    text = (ROOT / ".env.example").read_text()
    values = {k: secrets.token_urlsafe(36) for k in SECRET_KEYS}
    for k, v in values.items():
        text = re.sub(rf"^{k}=.*$", f"{k}={v}", text, flags=re.M)
    text = re.sub(
        r"^DATABASE_URL=.*$",
        f"DATABASE_URL=postgresql+psycopg://talentai:{values['POSTGRES_PASSWORD']}@127.0.0.1:18030/talentai",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^REDIS_URL=.*$",
        f"REDIS_URL=redis://:{values['REDIS_PASSWORD']}@127.0.0.1:18031/0",
        text,
        flags=re.M,
    )
    target.write_text(text)
    target.chmod(0o600)
    print(f"wrote {target} with {len(values)} random secrets (chmod 600). Keep it out of git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
