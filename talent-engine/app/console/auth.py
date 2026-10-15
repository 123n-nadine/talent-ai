"""Console sessions: a signed, expiring cookie. The browser never sees the tenant API key."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import Settings

COOKIE = "talent_console"


def _key(settings: Settings) -> bytes:
    secret = settings.console_session_secret or ("session:" + settings.tenant_api_key)
    return hashlib.sha256(secret.encode()).digest()


def issue(settings: Settings, user: str) -> str:
    payload = {
        "u": user,
        "exp": int(time.time()) + settings.console_session_hours * 3600,
        "n": secrets.token_hex(8),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(_key(settings), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify(settings: Settings, token: str | None) -> str | None:
    """Return the user name for a valid, unexpired token, else None."""
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(
        hmac.new(_key(settings), body.encode(), hashlib.sha256).hexdigest(), sig
    ):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except Exception:  # noqa: BLE001
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    return str(payload.get("u") or "")


def check_login(settings: Settings, user: str, password: str) -> bool:
    if not settings.console_password:
        return False
    return hmac.compare_digest(user, settings.console_user) and hmac.compare_digest(
        password, settings.console_password
    )


def id_token(settings: Settings, national_id: str) -> str:
    """What the host system would compute: HMAC-SHA256 of the national ID with its own secret."""
    return hmac.new(
        settings.console_id_token_secret.encode(), national_id.strip().encode(), hashlib.sha256
    ).hexdigest()
