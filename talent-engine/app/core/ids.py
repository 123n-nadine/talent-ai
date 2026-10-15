"""Prefixed, time-sortable identifiers (no personal data inside)."""

import secrets
import time


def new_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):011x}{secrets.token_hex(5)}"
