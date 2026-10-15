"""API-key hashing and HMAC signing of callbacks."""

import hashlib
import hmac
import time


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def sign_callback(secret: str, timestamp: str, body: bytes) -> str:
    """Signature over `<timestamp>.<body>` so the timestamp cannot be replaced on replay."""
    mac = hmac.new(secret.encode("utf-8"), timestamp.encode("utf-8") + b"." + body, hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def verify_callback(
    secret: str,
    timestamp: str,
    body: bytes,
    signature: str,
    max_age_s: int = 300,
    now: float | None = None,
) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = now if now is not None else time.time()
    if abs(current - ts) > max_age_s:
        return False
    expected = sign_callback(secret, timestamp, body)
    return hmac.compare_digest(expected, signature or "")
