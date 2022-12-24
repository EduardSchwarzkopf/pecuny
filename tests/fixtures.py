import pytest
import datetime
from app.oauth2 import create_access_token
from app import models, repository as repo
from app.routers.users import get_user_manager

import contextlib

from app.database import get_user_db
from app.schemas import UserCreate
from fastapi_users.exceptions import UserAlreadyExists
from httpx import AsyncClient

get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with get_user_db_context() as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(
                    UserCreate(
                        email=email, password=password, is_superuser=is_superuser
                    )
                )
                print(f"User created {user}")
                return user
    except UserAlreadyExists:
        print(f"User {email} already exists")


pytestmark = pytest.mark.anyio


@pytest.fixture
async def test_user(session):
    user_list = await repo.get_all(models.User)

    yield user_list[0] if len(user_list) > 0 else await create_user(
        "hello123@pytest.de", "password123"
    )


@pytest.fixture
async def token(test_user):
    yield create_access_token(
        {
            "user_id": str(test_user.id),
            "aud": ["fastapi-users:auth"],
        }
    )


@pytest.fixture
async def authorized_client(client: AsyncClient, token):
    client.cookies = {**client.cookies, "fastapiusersauth": token}

    yield client


@pytest.fixture
async def test_users(session):
    users_data = [
        ["user01@pytest.de", "password123"],
        ["user02@pytest.de", "password123"],
        ["user03@pytest.de", "password123"],
    ]

    for data in users_data:
        await create_user(data[0], data[1])

    yield await repo.get_all(models.User)


@pytest.fixture
async def test_account(test_user: models.User, session):
    account_data = {"label": "test_account", "description": "test", "balance": 5000}

    db_account = models.Account(
        user=test_user,
        **account_data,
    )

    session.add(db_account)

    await session.commit()

    yield await repo.get(models.Account, db_account.id)


@pytest.fixture
async def test_accounts(test_users, session):
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


@pytest.fixture
async def test_transactions(test_accounts, session):
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

        await repo.update(models.Account, account_id, **{"balance": new_balance})

        transaction_list.append(
            models.Transaction(
                information=db_transaction_information, account_id=account_id
            )
        )

    session.add_all(transaction_list)
    await session.commit()
