import anyio
import pytest
from httpx import AsyncClient
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from app import events
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.database import Base
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.test_db_url)
app.add_middleware(SQLAlchemyMiddleware, db_url=settings.test_db_url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await events.create_categories(async_session())


anyio.run(init_models)

pytestmark = pytest.mark.anyio


@pytest.fixture
async def session():
    yield async_session()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


from .fixtures import *
