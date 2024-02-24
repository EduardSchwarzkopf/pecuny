import datetime
from dataclasses import dataclass
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app import repository as repo
from app.oauth2 import create_access_token
from app.services.users import UserService


# TODO: Rename all append all fixtures functions with: _fixture
# this will be more clear later on what an fixture is
@pytest.fixture(name="aaaaa")
async def fixture_user_service():
    yield UserService()


@dataclass
class ClientSessionWrapper:
    client: AsyncClient = None
    authorized_client: AsyncClient = None
    session: AsyncSession = None


@pytest.fixture(name="test_user")
@pytest.mark.usefixtures("session")
async def fixture_test_user(user_service: UserService):
    user_list = await repo.get_all(models.User)

    if len(user_list) > 0:
        return user_list[0]
    else:
        return await user_service.create_user(
            "hello123@pytest.de", "password123", is_verified=True
        )


@pytest.fixture(name="token")
async def fixture_token(test_user):
    yield create_access_token(
        {
            "sub": str(test_user.id),
            "aud": ["fastapi-users:auth"],
        }
    )


@pytest.fixture(name="authorized_client")
async def fixture_authorized_client(client: AsyncClient, token):
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
    users_data = [
        ["user01@pytest.de", "password123"],
        ["user02@pytest.de", "password123"],
        ["user03@pytest.de", "password123"],
        ["user04@pytest.de", "password123"],
    ]

    user_list = []

    for data in users_data:
        user = await user_service.create_user(data[0], data[1], is_verified=True)
        user_list.append(user)

    yield user_list


@pytest.fixture(name="test_account")
async def fixture_test_account(test_user: models.User, session):
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
    return [(date_start - datetime.timedelta(days=idx)) for idx in range(days)]


@pytest.fixture(name="test_transactions")
async def fixture_test_transactions(test_accounts, session):
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
