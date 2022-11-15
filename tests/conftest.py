import pytest
from app import events
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.database import Base, db
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient


engine = create_async_engine(settings.test_db_url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


pytestmark = pytest.mark.anyio


@pytest.fixture
async def session():
    await db.init()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await events.create_categories(db.session)
    yield db.session


@pytest.fixture
async def client(session) -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def anyio_backend():
    return "asyncio"


from .fixtures import *
