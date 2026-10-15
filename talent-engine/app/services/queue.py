"""Dispatch screenings to the RQ worker, or run them inline (tests / tiny setups)."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings


def dispatch(
    settings: Settings, sessionmaker: Any, screening_id: str, background_tasks: Any = None
) -> str:
    if settings.queue_mode == "inline":
        from app.pipeline.runner import execute_with_retries

        if background_tasks is not None:
            background_tasks.add_task(execute_with_retries, sessionmaker, settings, screening_id)
        else:
            execute_with_retries(sessionmaker, settings, screening_id)
        return "inline"
    from redis import Redis
    from rq import Queue

    from app.worker.tasks import run_screening_task

    q = Queue(settings.queue_name, connection=Redis.from_url(settings.redis_url))
    q.enqueue(run_screening_task, screening_id, job_timeout=900, result_ttl=3600)
    return "rq"
