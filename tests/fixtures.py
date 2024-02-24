import datetime
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app import repository as repo
from app.oauth2 import create_access_token
from app.services.users import UserService
from app.utils.dataclasses_utils import ClientSessionWrapper, CreateUserData


@pytest.fixture(name="user_service")
async def fixture_user_service():
    """
    Fixture that provides a user service.

    Args:
        None

    Returns:
        UserService: An instance of the user service.
    """

    yield UserService()


@pytest.fixture(name="test_user")
@pytest.mark.usefixtures("session")
async def fixture_test_user(user_service: UserService):
    """
    Fixture that retrieves an existing user or creates a new user.

    Args:
        user_service: The user service fixture.

    Returns:
        User: An existing user or a newly created user.
    """
    user_list = await repo.get_all(models.User)

    if len(user_list) > 0:
        return user_list[0]

    return await user_service.create_user(
        CreateUserData("hello123@pytest.de", "password123", is_verified=True)
    )


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


@pytest.mark.usefixtures("session")
@pytest.fixture(name="test_users")
async def fixture_test_users(user_service: UserService):
    """
    Fixture that creates test users.

    Args:
        user_service: The user service fixture.

    Returns:
        List[User]: A list of test users.
    """

    users_data = [
        ["user01@pytest.de", "password123"],
        ["user02@pytest.de", "password123"],
        ["user03@pytest.de", "password123"],
        ["user04@pytest.de", "password123"],
    ]

    user_list = []

    for data in users_data:
        user = await user_service.create_user(
            CreateUserData(data[0], data[1], is_verified=True)
        )
        user_list.append(user)

    yield user_list


@pytest.fixture(name="test_account")
async def fixture_test_account(test_user: models.User, session):
    """
    Fixture that creates a test account.

    Args:
        test_user: The test user fixture.
        session: The session fixture.

    Returns:
        Account: A test account.
    """

    account_data = {"label": "test_account", "description": "test", "balance": 5000}

    db_account = models.Account(
        user=test_user,
        **account_data,
    )

    session.add(db_account)

    await session.commit()

    yield await repo.get(models.Account, db_account.id)


@pytest.fixture(name="test_accounts")
async def fixture_test_accounts(test_users: List[models.User], session):
    """
    Fixture that creates test accounts.

    Args:
        test_users: A list of test users.
        session: The session fixture.

    Returns:
        List[Account]: A list of test accounts.
    """

    accounts_data = [
        {
            "user": test_users[0],
            "label": "account_00",
            "description": "description_00",
            "balance": 100,
        },
        {
            "user": test_users[1],
            "label": "account_01",
            "description": "description_01",
            "balance": 200,
        },
        {
            "user": test_users[2],
            "label": "account_02",
            "description": "description_02",
            "balance": 500,
        },
        {
            "user": test_users[3],
            "label": "account_03",
            "description": "description_03",
            "balance": 1000,
        },
        {
            "user": test_users[0],
            "label": "account_04",
            "description": "description_04",
            "balance": 2000,
        },
    ]

    def create_accounts_model(account):
        return models.Account(**account)

    accounts_map = map(create_accounts_model, accounts_data)
    accounts = list(accounts_map)

    session.add_all(accounts)
    await session.commit()

    yield await repo.get_all(models.Account)


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
async def fixture_test_transactions(test_accounts, session):
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
            "account_id": 1,
            "amount": 200,
            "reference": "transaction_001",
            "date": dates[0],
            "category_id": 1,
        },
        {
            "account_id": 1,
            "amount": 100,
            "reference": "transaction_002",
            "date": dates[1],
            "category_id": 1,
        },
        {
            "account_id": 2,
            "amount": 50,
            "reference": "transaction_003",
            "date": dates[3],
            "category_id": 4,
        },
        {
            "account_id": 3,
            "amount": 100,
            "reference": "transaction_004",
            "date": dates[4],
            "category_id": 8,
        },
        {
            "account_id": 4,
            "amount": 500,
            "reference": "transaction_005",
            "date": dates[3],
            "category_id": 7,
        },
        {
            "account_id": 5,
            "amount": 200,
            "reference": "transaction_006",
            "date": dates[2],
            "category_id": 7,
        },
    ]

    transaction_list = []

    for transaction_info in transaction_data:
        account_id = transaction_info["account_id"]
        account_index = next(
            (i for i, item in enumerate(test_accounts) if item.id == account_id), -1
        )
        if account_index == -1:
            raise ValueError("No Account found with that Id")

        db_transaction_information = models.TransactionInformation()
        db_transaction_information.add_attributes_from_dict(transaction_info)

        new_balance = (
            test_accounts[account_index].balance + db_transaction_information.amount
        )

        update_info = {"balance": new_balance}
        await repo.update(models.Account, account_id, **update_info)

        transaction_list.append(
            models.Transaction(
                information=db_transaction_information, account_id=account_id
            )
        )

    session.add_all(transaction_list)
    await session.commit()
