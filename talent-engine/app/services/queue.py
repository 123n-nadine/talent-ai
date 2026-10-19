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


class QueueUnavailable(RuntimeError):
    """The job queue (Redis) could not take the screening."""


def dispatch_or_fail(
    db: Any, settings: Settings, sessionmaker: Any, screening_id: str, background_tasks: Any = None
) -> str:
    """Dispatch, and if the queue cannot take the job, mark the screening failed instead of leaving
    a «queued» row that no worker will ever see (final QA, Q7b: a Redis restart during the request
    left the screening queued forever, and the host's retry got the same stuck row back because an
    identical, non-failed screening is reused). The caller answers 503 so the host retries; the
    retry creates a new screening."""
    try:
        return dispatch(settings, sessionmaker, screening_id, background_tasks)
    except Exception as e:  # noqa: BLE001 — Redis down, restarting, refused, timed out
        from app.services import audit
        from app.storage.models import Screening

        db.rollback()
        s = db.get(Screening, screening_id)
        if s is not None and s.status == "queued":
            s.status = "failed"
            s.error = f"queue unavailable: {type(e).__name__}"
            audit.log(
                db,
                s.tenant_id,
                s.candidate.external_ref,
                "screening.failed",
                "system",
                {"screening_id": s.id, "error": s.error},
            )
            db.commit()
        raise QueueUnavailable(f"{type(e).__name__}: {e}") from e
