from typing import Any

from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError

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
            if is_model_instance(result):
                await db.session.refresh(result)

    except Exception as e:
        logger.error(
            "Error occurred during transaction for %s: %s", handler.__name__, e
        )
        result = {}
        if db.session:
            await db.session.rollback()

    return result


def is_model_instance(obj):
    """Check if the given object is a SQLAlchemy model instance.

    Args:
        obj: The object to check.

    Returns:
        bool: True if the object is a SQLAlchemy model instance, False otherwise.
    """
    try:
        object_mapper(obj)
        return True
    except UnmappedInstanceError:
        return False
