import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.data import categories
from app.database import db
from app.models import Base


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

    section_list = categories.get_section_list()
    category_list = categories.get_category_list()

    transaction_section_list = [
        models.TransactionSection(**section) for section in section_list
    ]
    transaction_category_list = [
        models.TransactionCategory(**category) for category in category_list
    ]

    session.add_all(transaction_category_list + transaction_section_list)
    await session.commit()


@pytest.fixture(scope="session", autouse=True)
async def fixture_init_db():
    """
    Fixture for initializing the database and populating it with test data.

    Yields:
        None
    """

    await db.init()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await populate_db(db.session)

    yield

    await db.engine.dispose()


async def cleanup_tests():
    """
    Performs cleanup tasks for tests.

    Returns:
        None
    """

    user_list = await repo.get_all(models.User)

    delete_task = [repo.delete(user) for user in user_list]
    await asyncio.gather(*delete_task)


@pytest.fixture(name="session", autouse=True, scope="session")
@pytest.mark.usefixtures("fixture_init_db")
async def fixture_session() -> AsyncSession:  # type: ignore
    """
    Fixture that provides an async session.

    Args:
        None

    Returns:
        AsyncSession: An async session.
    """
    await cleanup_tests()

    yield db.session


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
