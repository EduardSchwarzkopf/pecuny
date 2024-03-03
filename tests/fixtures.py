import asyncio
import datetime
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app import repository as repo
from app import schemas
from app import transaction_manager as tm
from app.oauth2 import create_access_token
from app.services.accounts import AccountService
from app.services.transactions import TransactionService
from app.services.users import UserService
from app.utils.dataclasses_utils import ClientSessionWrapper, CreateUserData


@pytest.fixture(name="test_user")
async def fixture_test_user(session: AsyncSession):
    """
    Fixture that retrieves an existing user or creates a new user.

    Args:
        user_service: The user service fixture.

    Returns:
        User: An existing user or a newly created user.
    """
    test_user_email = "hello123@pytest.de"
    user_list = await repo.filter_by(models.User, "email", test_user_email)

    if len(user_list) > 0:
        yield user_list[0]

    user_service = UserService()
    user = await tm.transaction(
        user_service.create_user,
        CreateUserData(test_user_email, "password123", is_verified=True),
    )

    yield user

    await user_service.delete_self(user)


@pytest.fixture(name="token")
async def fixture_token(test_user):
    """
    Fixture that generates an access token for a test user.

    Args:
        test_user: The test user fixture.

    Returns:
        str: An access token for the test user.
    """

    yield create_access_token(
        {
            "sub": str(test_user.id),
            "aud": ["fastapi-users:auth"],
        }
    )


@pytest.fixture(name="authorized_client")
async def fixture_authorized_client(client: AsyncClient, token):
    """
    Fixture that provides an authorized client with a token.

    Args:
        client: The async client fixture.
        token: The authentication token.

    Returns:
        AsyncClient: An authorized client with the provided token.
    """

    client.cookies = {**client.cookies, "fastapiusersauth": token}
    yield client


@pytest.fixture(name="client_session_wrapper")
async def fixture_client_session_wrapper_fixture(
    client: AsyncClient, authorized_client: AsyncClient, session: AsyncSession
):
    """
    Fixture that combines the client and session fixtures into a single object.

    Args:
        client: The async client fixture.
        session: The async session fixture.

    Returns:
        SessionClient: An object containing the client and session.
    """
    yield ClientSessionWrapper(client, authorized_client, session)


@pytest.fixture(name="test_users")
async def fixture_test_users(session: AsyncSession):
    """
    Fixture that creates test users.

    Args:
        user_service: The user service fixture.

    Returns:
        List[User]: A list of test users.
    """

    create_user_list = [
        ["user01@pytest.de", "password123", "User01"],
        ["user02@pytest.de", "password123", "User02"],
        ["user03@pytest.de", "password123", "User03"],
    ]

    user_service = UserService()
    for user in create_user_list:
        await tm.transaction(
            user_service.create_user,
            CreateUserData(
                email=user[0], password=user[1], displayname=user[2], is_verified=True
            ),
        )

    user_list = await repo.get_all(models.User)

    yield user_list

    delete_tasks = [user_service.delete_self(user) for user in user_list]
    await asyncio.gather(*delete_tasks)


@pytest.fixture(name="test_account")
async def fixture_test_account(session: AsyncSession, test_user: models.User):
    """
    Fixture that creates a test account.

    Args:
        test_user: The test user fixture.
        session: The session fixture.

    Returns:
        Account: A test account.
    """

    account_data = schemas.Account(
        user=test_user, label="test_account", description="test", balance=5000
    )

    service = AccountService()

    account = await tm.transaction(service.create_account, test_user, account_data)

    yield account

    service.delete_account(test_user, account.id)


@pytest.fixture(name="test_accounts")
async def fixture_test_accounts(
    session: AsyncSession, test_user, test_users: List[models.User]
):
    """
    Fixture that creates test accounts.

    Args:
        test_users: A list of test users.
        session: The session fixture.

    Returns:
        List[Account]: A list of test accounts.
    """

    account_data_list = [
        {
            "user": test_user,
            "label": "account_00",
            "description": "description_00",
            "balance": 100,
        },
        {
            "user": test_users[0],
            "label": "account_01",
            "description": "description_01",
            "balance": 200,
        },
        {
            "user": test_users[1],
            "label": "account_02",
            "description": "description_02",
            "balance": 500,
        },
        {
            "user": test_users[2],
            "label": "account_03",
            "description": "description_03",
            "balance": 1000,
        },
        {
            "user": test_user,
            "label": "account_04",
            "description": "description_04",
            "balance": 2000,
        },
    ]

    service = AccountService()

    # TODO: Make this Async
    account_list = [
        await tm.transaction(
            service.create_account,
            account_data["user"],
            schemas.Account(
                label=account_data["label"],
                description=account_data["description"],
                balance=account_data["balance"],
            ),
        )
        for account_data in account_data_list
    ]

    yield account_list

    delete_task = [
        service.delete_account(account.user, account) for account in account_list
    ]
    await asyncio.gather(*delete_task)


@pytest.fixture(name="test_account_transaction_list")
@pytest.mark.usefixtures("test_transactions")
async def fixture_test_account_transaction_list(test_account):

    yield await repo.filter_by(models.Transaction, "account_id", test_account.id)


async def get_date_range(date_start, days=5):
    """
    Returns a list of dates in a range starting from a given date.

    Args:
        date_start: The starting date.
        days: The number of days in the range (default is 5).

    Returns:
        List[datetime.date]: A list of dates in the range.
    """

    return [(date_start - datetime.timedelta(days=idx)) for idx in range(days)]


@pytest.fixture(name="test_transactions")
async def fixture_test_transactions(session: AsyncSession, test_accounts, test_account):
    """
    Fixture that creates test transactions.

    Args:
        test_accounts: The test accounts fixture.
        session: The session fixture.

    Returns:
        List[Transaction]: A list of test transactions.
    """

    dates = await get_date_range(datetime.datetime.now(datetime.timezone.utc))

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

    for account in test_accounts + [test_account]:
        create_transactions_task = [
            tm.transaction(
                service.create_transaction,
                account.user,
                schemas.TransactionInformationCreate(
                    **transaction, account_id=account.id
                ),
            )
            for transaction in transaction_data
        ]

        await asyncio.gather(*create_transactions_task)

    transaction_list = await repo.get_all(models.Transaction)

    yield transaction_list

    delete_task = [service.delete_transaction(account) for account in transaction_list]
    await asyncio.gather(*delete_task)
