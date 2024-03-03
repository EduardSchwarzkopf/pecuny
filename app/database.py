import sys

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


class Database:
    def __init__(self, url: str) -> None:
        """
        Initializer/Constructor for Database class.

        Parameters:
        url: str - The URL of the database.
        """
        self.url = url
        self.engine = None
        self.session = None

    async def init(self):
        """
        Asynchronous method to initialize the database connection and assign a new session.
        """
        # Close the session to avoid creating repeated connections
        if self.session:
            await self.session.close()

        self.engine = create_async_engine(self.url, future=True)
        self.session = await self.get_session()

    async def get_session(self) -> AsyncSession:
        """
        Creates and provides a new database session.

        Returns:
        AsyncSession: A database session
        """
        session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        async with session_factory() as session:
            try:
                return session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()


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


SQLALCHEMY_DATABASE_URL = settings.db_url


if "pytest" in sys.modules:
    SQLALCHEMY_DATABASE_URL = settings.test_db_url

db: Database = Database(SQLALCHEMY_DATABASE_URL)
