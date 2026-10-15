"""RQ task entry points."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.storage.db import make_engine, make_sessionmaker


@lru_cache
def _sessionmaker():
    return make_sessionmaker(make_engine(get_settings().database_url))


def run_screening_task(screening_id: str) -> str:
    from app.pipeline.runner import execute_with_retries

    return execute_with_retries(_sessionmaker(), get_settings(), screening_id)
