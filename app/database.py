import sys

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

Base = declarative_base()


class Database:
    def __init__(self, url):
        self.session = None
        self.engine = None
        self.url = url

    async def init(self):
        # closes connections if a session is created,
        # so as not to create repeated connections
        if self.session:
            await self.session.close()

        self.engine = create_async_engine(self.url, future=True)
        self.session = self.get_session()

    def get_session(self) -> AsyncSession:
        return sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)()


async def get_user_db():
    from app.models import OAuthAccount, User

    yield SQLAlchemyUserDatabase(db.session, User, OAuthAccount)


SQLALCHEMY_DATABASE_URL = settings.db_url


if "pytest" in sys.modules:
    SQLALCHEMY_DATABASE_URL = settings.test_db_url

db: Database = Database(SQLALCHEMY_DATABASE_URL)
