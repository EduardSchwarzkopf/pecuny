from typing import Any

from app import models
from app.database import db
from app.logger import get_logger

logger = get_logger(__name__)


async def transaction(handler, *args: Any) -> Any:
    """Execute a transaction for the specified handler function.

    Args:
        handler: The handler function to execute within the transaction.
        *args: Additional arguments to pass to the handler function.

    Returns:
        Any: The result of the handler function.

    Raises:
        None
    """
    try:
        result = await handler(*args)
        if db.session:
            await db.session.commit()
            if _is_models_object(result):
                await db.session.refresh(result)

    except Exception as e:
        logger.error(
            "Error occurred during transaction for %s: %s", handler.__name__, e
        )
        result = {}
        if db.session:
            await db.session.rollback()

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
