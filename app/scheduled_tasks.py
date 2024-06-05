from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logger import get_logger
from app.tasks import create_transactions_for_batch

logger = get_logger(__name__)
job_registry = []


def add_jobs_to_scheduler(scheduler: AsyncIOScheduler):
    for func, trigger, kwargs in job_registry:
        scheduler.add_job(func, trigger, **kwargs)
    scheduler.start()


def register_job(trigger, **kwargs):
    def decorator(func):
        job_registry.append((func, trigger, kwargs))
        return func

    return decorator


async def create_scheduled_transactions():
    create_transactions_for_batch.delay()
