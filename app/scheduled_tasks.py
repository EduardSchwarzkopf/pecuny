from typing import Any, List, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.tasks import process_scheduled_transactions

job_registry: List[Tuple[Any, Any, dict]] = []


def add_jobs_to_scheduler(scheduler: AsyncIOScheduler):
    """
    Add registered jobs to the scheduler and start it.

    Args:
        scheduler: The scheduler to add jobs to.
    """

    for func, trigger, kwargs in job_registry:
        scheduler.add_job(func, trigger, **kwargs)
    scheduler.start()


def register_job(trigger, **kwargs):
    """
    Decorator function to register a job with specified trigger and arguments.

    Args:
        trigger: The trigger for the job.
        **kwargs: Additional keyword arguments for the job.

    Returns:
        The decorated function.
    """

    def decorator(func):
        """
        Decorator function to register a job with specified trigger and arguments.
        """

        job_registry.append((func, trigger, kwargs))
        return func

    return decorator


@register_job("interval", days=1)
async def create_scheduled_transactions():
    """
    Create scheduled transactions daily by triggering the processing of scheduled transactions.
    """
    process_scheduled_transactions.delay()
