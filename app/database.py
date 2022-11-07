from typing import List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .config import settings
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

SQLALCHEMY_DATABASE_URL = settings.db_url

Base = declarative_base()


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def init(self):
        self._engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            future=True,
        )
        self._session = sessionmaker(self._engine, class_=AsyncSession)()


db = AsyncDatabaseSession()


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: List[OAuthAccount] = relationship("OAuthAccount", lazy="joined")


async def get_user_db():
    yield SQLAlchemyUserDatabase(db._session, User, OAuthAccount)
