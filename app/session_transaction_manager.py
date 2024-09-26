from contextlib import asynccontextmanager
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError

from app.database import db
from app.logger import get_logger

logger = get_logger(__name__)


class SessionTransactionManager:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session or db.session
        self.entities_to_refresh = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
            logger.warning(f"Transaction rolled back due to: {exc_val}")
        else:
            await self.session.commit()
            for entity in self.entities_to_refresh:
                await self.session.refresh(entity)

    def add_for_refresh(self, entity):
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
    async with SessionTransactionManager(session=session) as txn:
        yield txn
