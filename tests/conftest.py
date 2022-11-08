from httpx import AsyncClient
from app import events
from app.config import settings
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from app.main import app
from app.database import Base
import pytest_asyncio

engine = create_async_engine(settings.test_db_url)
app.add_middleware(SQLAlchemyMiddleware, custom_engine=engine)


@pytest_asyncio.fixture()
async def async_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with db():
        await events.create_categories(db.session)


@pytest_asyncio.fixture()
async def client(async_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


from .fixtures import *
