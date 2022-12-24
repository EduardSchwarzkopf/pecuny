import pytest
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.database import Base, db
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from app.data import categories


engine = create_async_engine(settings.test_db_url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


pytestmark = pytest.mark.anyio


async def populate_db(session: AsyncSession):
    section_list = categories.get_section_list()
    category_list = categories.get_category_list()

    def create_section_model(section):
        return models.TransactionSection(**section)

    def create_category_model(category):
        return models.TransactionCategory(**category)

    section = list(map(create_section_model, section_list))
    category = list(map(create_category_model, category_list))

    session.add_all(section + category)
    await session.commit()


@pytest.fixture
async def session():
    await db.init()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await populate_db(db.session)
    yield db.session


@pytest.fixture
async def client(session) -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def anyio_backend():
    return "asyncio"


from .fixtures import *
