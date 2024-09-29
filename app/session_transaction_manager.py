from contextlib import asynccontextmanager
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError

from app import models
from app.database import db
from app.logger import get_logger

logger = get_logger(__name__)


class SessionTransactionManager:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session or db.session
        self.entities_to_refresh: List[models.Base] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
            # TODO: Add condition to log only unhandled erros?
            logger.warning("Transaction rolled back due to: %s", exc_val)
        else:
            await self.session.commit()
            for entity in self.entities_to_refresh:
                await self.session.refresh(entity)

    def add_for_refresh(self, entity):
        """
        Adds an entity to the list of entities to be refreshed.

        Args:
            entity: The entity to be added for refresh.

        Returns:
            None
        """

        if is_model_instance(entity):
            self.entities_to_refresh.append(entity)


def is_model_instance(obj):
    """Check if the given object is a SQLAlchemy model instance."""
    try:
        object_mapper(obj)
        return True
    except UnmappedInstanceError:
        return False


@asynccontextmanager
async def transaction(session: Optional[AsyncSession] = None):
    """
    A context manager that handles transactions using a SessionTransactionManager.

    Args:
        session: An optional AsyncSession object. Defaults to None.

    Yields:
        The transaction object.
    """

    async with SessionTransactionManager(session=session) as txn:
        yield txn
