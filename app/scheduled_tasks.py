from typing import Any, List, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logger import get_logger
from app.tasks import process_scheduled_transactions

logger = get_logger(__name__)
job_registry: List[Tuple[Any, Any, dict]] = []


def add_jobs_to_scheduler(scheduler: AsyncIOScheduler):
    for func, trigger, kwargs in job_registry:
        scheduler.add_job(func, trigger, **kwargs)
    scheduler.start()


def register_job(trigger, **kwargs):
    def decorator(func):
        job_registry.append((func, trigger, kwargs))
        return func

    return decorator


@register_job("interval", days=1)
async def create_scheduled_transactions():
    process_scheduled_transactions.delay()
