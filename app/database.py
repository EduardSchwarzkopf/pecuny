from typing import List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from fastapi_async_sqlalchemy import db
from .config import settings
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseOAuthAccountTableUUID,
)

SQLALCHEMY_DATABASE_URL = settings.db_url

Base = declarative_base()


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: List[OAuthAccount] = relationship("OAuthAccount", lazy="joined")


async def get_user_db():
    yield SQLAlchemyUserDatabase(db.session, User, OAuthAccount)
