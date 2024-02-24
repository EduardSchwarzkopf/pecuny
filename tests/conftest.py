import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.data import categories
from app.database import db
from app.main import app
from app.models import Base

engine = create_async_engine(settings.test_db_url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


pytestmark = pytest.mark.anyio


async def populate_db(session: AsyncSession):
    """
    Populates the database with transaction sections and categories.

    Args:
        session: Database session.

    Returns:
        None
    """

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


@pytest.fixture(name="session", scope="class")
async def fixture_session() -> AsyncSession:  # type: ignore
    """
    Fixture that provides an async session.

    Args:
        None

    Returns:
        AsyncSession: An async session.
    """

    await db.init()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await populate_db(db.session)
    yield db.session


@pytest.fixture(name="client")
@pytest.mark.usefixtures("module")
async def fixture_client() -> AsyncClient:  # type: ignore
    """
    Fixture that provides an async HTTP client.

    Args:
        None

    Returns:
        AsyncClient: An async HTTP client.
    """

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    """
    Fixture that provides the anyio backend.

    Args:
        None

    Returns:
        str: The anyio backend.
    """

    return "asyncio"


from .fixtures import *  # pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
