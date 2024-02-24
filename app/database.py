import sys

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


class Database:
    def __init__(self, url):
        self.session = None
        self.engine = None
        self.url = url

    async def init(self):
        """Initialize the database connection.

        Args:
            self

        Returns:
            None

        Raises:
            None
        """
        # closes connections if a session is created,
        # so as not to create repeated connections
        if self.session:
            await self.session.close()

        self.engine = create_async_engine(self.url, future=True)
        self.session = self.get_session()

    def get_session(self) -> AsyncSession:
        """Get the database session.

        Args:
            self

        Returns:
            AsyncSession: The database session.

        Raises:
            None
        """
        return sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)()


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
