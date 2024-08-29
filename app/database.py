from typing import Optional

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


class Database:
    def __init__(self, url: str) -> None:
        """
        Initialize the database connection.

        Args:
            url (str): The URL of the database.

        Raises:
            None
        """

        self.url = url
        self.engine = create_async_engine(url, future=True)
        self._session: Optional[AsyncSession] = None

    async def init(self):
        """
        Initialize the database connection.

        Raises:
            None
        """

        if self._session is not None:
            await self._session.close()

        self._session = self.get_session()

    def get_session(self) -> AsyncSession:
        """
        Get the asynchronous session for the database.

        Returns:
            AsyncSession: The asynchronous session for the database.

        Raises:
            RuntimeError: If the engine has not been initialized.
        """

        if self.engine is None:
            raise RuntimeError("Engine has not been initialized")

        session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        return session_factory()

    @property
    def session(self) -> AsyncSession:
        """
        Get the asynchronous session for the database.

        Returns:
            AsyncSession: The asynchronous session for the database.

        Raises:
            RuntimeError: If the database session has not been initialized.
        """

        if self._session is None:
            raise RuntimeError("Database session has not been initialized.")
        return self._session


async def get_user_db():
    """Get the user database.

    Args:
        None

    Returns:
        SQLAlchemyUserDatabase: The user database.

    Raises:
        None
    """
    from app.models import OAuthAccount, User  # pylint: disable=import-outside-toplevel

    yield SQLAlchemyUserDatabase(db.session, User, OAuthAccount)


db: Database = Database(settings.db_url)
