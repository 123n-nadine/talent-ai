"""`python -m app.worker` starts an RQ worker on the screenings queue."""

from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.core.logging import setup_logging

if __name__ == "__main__":
    settings = get_settings()
    setup_logging(settings.log_level)
    conn = Redis.from_url(settings.redis_url)
    worker = Worker([Queue(settings.queue_name, connection=conn)], connection=conn)
    worker.work(with_scheduler=False)
