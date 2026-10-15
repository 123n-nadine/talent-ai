"""HMAC-signed result push to the host system, with retries."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import orjson

from app.core.config import Settings
from app.core.security import sign_callback

log = logging.getLogger(__name__)


def send(
    url: str,
    secret: str,
    payload: dict[str, Any],
    settings: Settings,
    event: str = "screening.result",
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    body = orjson.dumps(payload)
    backoff = settings.retry_backoff or [1.0]
    attempts = 0
    last_error: str | None = None
    own = client is None
    client = client or httpx.Client(timeout=settings.callback_timeout_s)
    try:
        for i in range(settings.max_attempts):
            attempts = i + 1
            ts = str(int(time.time()))
            headers = {
                "Content-Type": "application/json",
                "X-Talent-Signature": sign_callback(secret, ts, body),
                "X-Talent-Timestamp": ts,
                "X-Talent-Event": event,
            }
            try:
                resp = client.post(url, content=body, headers=headers)
                if 200 <= resp.status_code < 300:
                    return {"ok": True, "attempts": attempts, "status_code": resp.status_code}
                last_error = f"HTTP {resp.status_code}"
            except httpx.HTTPError as e:
                last_error = f"{type(e).__name__}: {e}"
            log.warning("callback attempt %s failed: %s", attempts, last_error)
            if i < settings.max_attempts - 1:
                time.sleep(backoff[min(i, len(backoff) - 1)])
    finally:
        if own:
            client.close()
    return {"ok": False, "attempts": attempts, "error": last_error}
