import os
import logging
from celery import Celery
from celery.signals import setup_logging

from strategy import Mtd

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)

redis_url = f"redis://{redis_host}:{redis_port}"
celery = Celery("tasks", result_backend=redis_url, broker=redis_url)


@setup_logging.connect
def configure_loggers(*args, **kwargs):
    logging.basicConfig(level=logging.INFO)


@celery.task
def run_mtd(p1: list[int], p2: list[int], last_step: int):
    return Mtd().run(set(p1), set(p2), last_step)
