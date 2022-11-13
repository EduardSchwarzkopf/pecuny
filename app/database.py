import sys
from typing import List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship
from .config import settings
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseOAuthAccountTableUUID,
)

Base = declarative_base()


class Database:
    def __init__(self, url):
        self.session = None
        self.engine = None
        self.url = url

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def init(self):
        # closes connections if a session is created,
        # so as not to create repeated connections
        if self.session:
            await self.session.close()

        self.engine = create_async_engine(self.url, future=True)
        self.session = self.get_session()

    def get_session(self) -> AsyncSession:
        return sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)()


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: List[OAuthAccount] = relationship("OAuthAccount", lazy="joined")


async def get_user_db():
    yield SQLAlchemyUserDatabase(db.session, User, OAuthAccount)


SQLALCHEMY_DATABASE_URL = settings.db_url


if "pytest" in sys.modules:
    SQLALCHEMY_DATABASE_URL = settings.test_db_url

db: Database = Database(SQLALCHEMY_DATABASE_URL)
