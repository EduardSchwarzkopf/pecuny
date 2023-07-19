from typing import Any

from app import models
from app.database import db
from app.logger import get_logger

logger = get_logger(__name__)


async def transaction(handler, *args: Any) -> Any:
    logger.info("Starting transaction for %s with args %s", handler.__name__, args)
    try:
        result = await handler(*args)
        await db.session.commit()
        if _is_models_object(result):
            await db.session.refresh(result)
            logger.info(
                "Transaction for %s successful, result refreshed", handler.__name__
            )

    except Exception as e:
        logger.error(
            "Error occurred during transaction for %s: %s", handler.__name__, e
        )
        result = {}
        await db.session.rollback()
    finally:
        await db.engine.dispose()
        logger.info("Transaction for %s finished, engine disposed", handler.__name__)
        return result


def _is_models_object(db_object):
    return getattr(db_object, "__module__", None) == models.__name__
