import asyncio
import datetime
import itertools

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.repository import Repository
from app.services.accounts import AccountService
from app.services.transactions import TransactionService
from app.services.users import UserService
from app.utils.dataclasses_utils import CreateUserData
from app.utils.enums import DatabaseFilterOperator

# Reference: https://github.com/EduardSchwarzkopf/pecuny/issues/88
# pylint: disable=unused-argument


@pytest.fixture(name="common_user_data", scope="session")
def fixture_common_user_data():
    """
    Fixture for common user data used in tests.

    Returns:
        UserCreate: A UserCreate instance with common user data.
    """

    return schemas.UserCreate(
        email="user123@example.com",
        password="mypassword",
        displayname="user",
    )


@pytest.fixture(name="user_service", scope="session")
async def fixture_user_service(session):
    """
    Create a session-scoped user service fixture.

    Args:
        session: The session object.

    Returns:
        UserService: The user service fixture.

    """
    yield UserService()


@pytest.fixture(name="create_test_users", scope="session")
async def fixture_create_test_users(user_service: UserService):
    """
    Fixture that creates test users.

    Args:
        None

    Yields:
        None
    """

    password = "password123"
    create_user_list = [
        ["user00@pytest.de", password, "User00"],
        ["user01@pytest.de", password, "User01"],
        ["user02@pytest.de", password, "User02"],
        ["user03@pytest.de", password, "User03"],
        ["hello123@pytest.de", password, "LoginUser"],
    ]

    user_list = []
    for user in create_user_list:
        user_list.append(
            await user_service.create_user(
                CreateUserData(
                    email=user[0],
                    password=user[1],
                    displayname=user[2],
                    is_verified=True,
                ),
            )
        )

    yield user_list


@pytest.fixture(name="test_users")
async def fixture_test_user_list(create_test_users, repository: Repository):
    """
    Fixture for retrieving a list of test users.

    Args:
        create_test_users (fixture): Fixture to create test users.

    Yields:
        list[models.User]: A list of test users.
    """
    yield await repository.get_all(models.User)


@pytest.fixture(name="test_user")
async def fixture_test_user(create_test_users, repository: Repository):
    """
    Fixture for retrieving a test user.

    Args:
        create_test_users (fixture): Fixture to create test users.

    Yields:
        models.User: The test user.

    """
    user_list = await repository.filter_by(
        models.User, models.User.is_verified, True, DatabaseFilterOperator.EQUAL
    )

    yield user_list[0]


async def create_and_yield_user(
    user_service: UserService, user_data: schemas.UserCreate
):
    """
    Creates a user using the provided user data and yields the user object.

    Args:
        user_service: The UserService instance for user management.
        user_data: The UserCreate schema containing user data.

    Yields:
        User: The created user object.

    Raises:
        None
    """

    user = await user_service.create_user(user_data)
    yield user

    if user:
        await user_service.delete_self(user)


@pytest.fixture(name="active_user")
async def fixture_active_user(
    user_service: UserService, common_user_data: schemas.UserCreate
):
    """
    Fixture for providing an active user for testing.

    Args:
        user_service: The UserService instance for user management.
        common_user_data: The common user data for creating the active user.

    Yields:
        User: The active user object for testing.
    """

    common_user_data.is_active = True
    async for user in create_and_yield_user(user_service, common_user_data):
        yield user


@pytest.fixture(name="active_verified_user")
async def fixture_active_verified_user(
    user_service: UserService, common_user_data: schemas.UserCreate
):
    """
    Fixture for providing an active and verified user for testing.

    Args:
        user_service: The UserService instance for user management.
        common_user_data: The common user data for creating the active and verified user.

    Yields:
        User: The active and verified user object for testing.
    """

    common_user_data.is_verified = True
    common_user_data.is_active = True
    async for user in create_and_yield_user(user_service, common_user_data):
        yield user


@pytest.fixture(name="inactive_user")
async def fixture_inactive_user(
    user_service: UserService, common_user_data: schemas.UserCreate
):
    """
    Fixture for providing an inactive user for testing.

    Args:
        user_service: The UserService instance for user management.
        common_user_data: The common user data for creating the inactive user.

    Yields:
        User: The inactive user object for testing.
    """

    common_user_data.is_active = False
    async for user in create_and_yield_user(user_service, common_user_data):
        yield user


@pytest.fixture(name="create_test_accounts", scope="session")
async def fixture_create_test_accounts(
    session: AsyncSession, create_test_users: list[models.User]
):
    """
    Fixture that creates test accounts.

    Args:
        session (fixture): The session fixture.
        test_users (fixture): Fixture to get a test user.
        test_users (fixuter): Fixture to get a list of test users.

    Returns:
        list[Account]: A list of test accounts.
    """

    account_data_list: list[dict[str, str | int]] = [
        {
            "label": "account_00",
            "description": "description_00",
            "balance": 100,
        },
        {
            "label": "account_01",
            "description": "description_01",
            "balance": 200,
        },
        {
            "label": "account_02",
            "description": "description_02",
            "balance": 500,
        },
        {
            "label": "account_03",
            "description": "description_03",
            "balance": 1000,
        },
        {
            "label": "account_04",
            "description": "description_04",
            "balance": 2000,
        },
    ]

    service = AccountService()

    create_task_list = []

    for user, account_data in itertools.product(create_test_users, account_data_list):
        task = service.create_account(
            user,
            schemas.Account(
                label=account_data["label"],
                description=account_data["description"],
                balance=account_data["balance"],
            ),
        )
        create_task_list.append(task)
    await asyncio.gather(*create_task_list)

    await session.commit()

    yield


@pytest.fixture(name="test_account")
async def fixture_test_account(
    test_user: models.User, create_test_accounts, repository: Repository
):
    """
    Fixture for retrieving a test account.

    Args:
        test_user (fixture): The test user.
        create_test_accounts (fixture): The fixture for creating test accounts.

    Yields:
        models.Account: The test account.

    """

    account = await repository.filter_by(
        models.Account,
        models.Account.user_id,
        test_user.id,
        load_relationships_list=[models.Account.user],
    )
    yield account[0]


@pytest.fixture(name="test_accounts")
async def fixture_get_test_account_list(create_test_accounts, repository: Repository):
    """
    Fixture for retrieving a list of test accounts.

    Args:
        create_test_accounts (fixuter): The fixture for creating test accounts.

    Yields:
        list[models.Account]: A list of test accounts.

    """

    yield await repository.get_all(
        models.Account, load_relationships_list=[models.Account.user]
    )


def get_date_range(date_start, days=5):
    """
    Returns a list of dates in a range starting from a given date.

    Args:
        date_start: The starting date.
        days: The number of days in the range (default is 5).

    Returns:
        list[datetime.date]: A list of dates in the range.
    """

    return [(date_start - datetime.timedelta(days=idx)) for idx in range(days)]


@pytest.fixture(name="create_transactions")
async def fixture_create_transactions(
    test_accounts: list[models.Account],
    session: AsyncSession,
):
    """
    Fixture that creates test transactions.

    Args:
        test_accounts (fixture): The test accounts fixture.
        session (fixture): The session fixture.

    Returns:
        list[Transaction]: A list of test transactions.
    """

    dates = get_date_range(datetime.datetime.now(datetime.timezone.utc))

    transaction_data = [
        {
            "amount": 200,
            "reference": "transaction_001",
            "date": dates[0],
            "category_id": 1,
        },
        {
            "amount": 100,
            "reference": "transaction_002",
            "date": dates[1],
            "category_id": 1,
        },
        {
            "amount": 50,
            "reference": "transaction_003",
            "date": dates[3],
            "category_id": 4,
        },
        {
            "amount": 100,
            "reference": "transaction_004",
            "date": dates[4],
            "category_id": 8,
        },
        {
            "amount": 500,
            "reference": "transaction_005",
            "date": dates[3],
            "category_id": 7,
        },
        {
            "amount": 200,
            "reference": "transaction_006",
            "date": dates[2],
            "category_id": 7,
        },
    ]

    service = TransactionService()
    create_task = []

    for account in test_accounts:
        create_task.extend(
            [
                service.create_transaction(
                    account.user,
                    schemas.TransactionInformationCreate(
                        account_id=account.id,
                        amount=transaction["amount"],
                        reference=transaction["reference"],
                        date=transaction["date"],
                        category_id=transaction["category_id"],
                    ),
                )
                for transaction in transaction_data
            ]
        )

    await asyncio.gather(*create_task)
    await session.commit()

    yield


@pytest.fixture(name="test_account_transaction_list")
async def fixture_test_account_transaction_list(
    create_transactions, test_account, repository: Repository
):
    """
    Fixture for retrieving a list of transactions associated with a test account.

    Args:
        create_transactions (fixture): The fixture for creating transactions.
        test_account (fixture): The test account.

    Yields:
        list[models.Transaction]: A list of transactions associated with the test account.
    """

    yield await repository.filter_by(
        models.Transaction, models.Transaction.account_id, test_account.id
    )


@pytest.fixture(name="transaction_list")
async def fixture_get_all_transactions(create_transactions, repository: Repository):
    """
    Fixture for retrieving a list of transactions.

    Args:
        create_transactions (fixture): The fixture for creating transactions.

    Yields:
        list[models.Transaction]: A list of transactions.

    """

    yield await repository.get_all(models.Transaction)
