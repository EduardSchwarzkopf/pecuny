import pytest

from app.data import categories, frequencies
from app.database import db
from app.models import Base
from app.repository import Repository

BASE_URL = "http://test"


async def populate_db():
    """
    Populates the database with transaction sections and categories.

    Args:
        session: Database session.

    Returns:
        None
    """

    section_list = categories.get_section_list()
    category_list = categories.get_category_list()
    frequency_list = frequencies.get_frequency_list()

    transaction_section_list = [
        models.TransactionSection(**section) for section in section_list
    ]
    transaction_category_list = [
        models.TransactionCategory(**category) for category in category_list
    ]
    transaction_frequency_list = [
        models.Frequency(**frequency) for frequency in frequency_list
    ]

    async with db.get_session() as session, session.begin():
        session.add_all(
            transaction_category_list
            + transaction_section_list
            + transaction_frequency_list
        )


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

    await populate_db()

    await db.engine.dispose()


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


@pytest.fixture(name="repository")
def get_repository():
    """
    Fixture to provide a repository instance for testing.

    Returns:
        Repository: An instance of the Repository class.
    """

    yield Repository()


from .fixtures import *  # pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
