from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import db
from app.logger import get_logger

logger = get_logger(__name__)


async def transaction(
    handler, session: AsyncSession = Depends(db.get_session), *args: Any
) -> Any:
    """Execute a transaction for the specified handler function.

    Args:
        handler: The handler function to execute within the transaction.
        *args: Additional arguments to pass to the handler function.

    Returns:
        Any: The result of the handler function.

    Raises:
        None
    """
    logger.info("Starting transaction for %s with args %s", handler.__name__, args)
    try:
        result = await handler(*args)
        await session.commit()
        if _is_models_object(result):
            await session.refresh(result)
            logger.info(
                "Transaction for %s successful, result refreshed", handler.__name__
            )

    except Exception as e:
        logger.error(
            "Error occurred during transaction for %s: %s", handler.__name__, e
        )
        result = {}
        await session.rollback()
    finally:
        logger.info("Transaction for %s finished, engine disposed", handler.__name__)

    return result


def _is_models_object(db_object):
    """Check if the given object is a SQLAlchemy model object.

    Args:
        db_object: The object to check.

    Returns:
        bool: True if the object is a SQLAlchemy model object, False otherwise.

    Raises:
        None
    """
    return getattr(db_object, "__module__", None) == models.__name__
