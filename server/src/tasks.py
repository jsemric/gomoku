import os
from celery import Celery

from mtd import Mtd

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)

redis_url = f"redis://{redis_host}:{redis_port}"
celery = Celery("tasks", result_backend=redis_url, broker=redis_url)


@celery.task
def run_mtd(p1: list[int], p2: list[int], last_step: int):
    return Mtd().run(set(p1), set(p2), last_step)
