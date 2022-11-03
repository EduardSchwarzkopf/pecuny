import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.config import settings
from app.database import Base
from app import events

SQLALCHEMY_DATABASE_URL = f"{settings.db_url}_test"


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init(self):
        self._engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            future=True,
        )
        self._session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )()


db = AsyncDatabaseSession()


@pytest.fixture()
def session():
    db.init()
    Base.metadata.drop_all(bind=db._engine)
    Base.metadata.create_all(bind=db._engine)

    events.create_categories(db._session)

    yield db._session


@pytest.fixture()
def client(session):
    yield TestClient(app)


from .fixtures import *
