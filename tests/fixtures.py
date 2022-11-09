import pytest
import datetime
from app.oauth2 import create_access_token
from app import models, repository as repo

pytestmark = pytest.mark.anyio


@pytest.fixture
async def test_user(client):
    user_data = {
        "email": "hello123@pytest.de",
        "password": "password123",
    }

    res = await client.post("/auth/register", json=user_data)

    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    yield new_user


@pytest.fixture
async def token(test_user):
    token = create_access_token(
        {
            "user_id": test_user["id"],
            "aud": ["fastapi-users:auth"],
        }
    )
    yield token


@pytest.fixture
async def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": "Bearer " + token}

    yield client


@pytest.fixture
async def test_users(session):
    users_data = [
        {
            "email": "user01@pytest.de",
            "password": "password123",
        },
        {
            "email": "user02@pytest.de",
            "password": "password123",
        },
        {
            "email": "user03@pytest.de",
            "password": "password123",
        },
    ]

    async def create_users_model(user):
        return models.User(**user)

    users_map = map(create_users_model, users_data)
    users = list(users_map)

    session.add_all(users)

    session.commit()

    user_list = await repo.get_all(models.User)
    yield user_list


@pytest.fixture
async def test_account(test_user, session):
    account_data = {"label": "test_account", "description": "test", "balance": 5000}

    result = await session.get(models.User, test_user["id"])
    user = result.scalar()

    db_account = models.Account(
        user=user,
        **account_data,
    )

    session.add(db_account)

    await session.commit()

    account = await repo.get(models.Account, db_account.id)

    yield account


@pytest.fixture
async def test_accounts(test_users, session):
    accounts_data = [
        {
            "user_id": test_users[0].id,
            "label": "account_00",
            "description": "description_00",
            "balance": 100,
        },
        {
            "user_id": test_users[1].id,
            "label": "account_01",
            "description": "description_01",
            "balance": 200,
        },
        {
            "user_id": test_users[2].id,
            "label": "account_02",
            "description": "description_02",
            "balance": 500,
        },
        {
            "user_id": test_users[3].id,
            "label": "account_03",
            "description": "description_03",
            "balance": 1000,
        },
        {
            "user_id": test_users[0].id,
            "label": "account_04",
            "description": "description_04",
            "balance": 2000,
        },
    ]

    async def create_accounts_model(account):
        return models.Account(**account)

    accounts_map = map(create_accounts_model, accounts_data)
    accounts = list(accounts_map)

    async with session:
        await session.add_all(accounts)
        await session.commit()

        account_list = await repo.get_all(models.Account)
        yield account_list


async def get_date_range(date_start, days=5):
    return [
        (date_start - datetime.timedelta(days=idx)).isoformat() for idx in range(days)
    ]


@pytest.fixture
async def test_transactions(test_accounts, session):
    dates = get_date_range(datetime.datetime.utcnow())

    transaction_data = [
        {
            "account_id": 1,
            "amount": 200,
            "reference": "transaction_001",
            "date": dates[0],
            "subcategory_id": 1,
        },
        {
            "account_id": 1,
            "amount": 100,
            "reference": "transaction_002",
            "date": dates[1],
            "subcategory_id": 1,
        },
        {
            "account_id": 2,
            "amount": 50,
            "reference": "transaction_003",
            "date": dates[3],
            "subcategory_id": 4,
        },
        {
            "account_id": 3,
            "amount": 100,
            "reference": "transaction_004",
            "date": dates[4],
            "subcategory_id": 8,
        },
        {
            "account_id": 4,
            "amount": 500,
            "reference": "transaction_005",
            "date": dates[3],
            "subcategory_id": 7,
        },
        {
            "account_id": 5,
            "amount": 200,
            "reference": "transaction_006",
            "date": dates[2],
            "subcategory_id": 7,
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

        del transaction_info["account_id"]
        db_transaction_information = models.TransactionInformation(**transaction_info)

        new_balance = (
            test_accounts[account_index].balance + db_transaction_information.amount
        )
        await repo.update(models.Account, account_id, {"balance": new_balance})

        transaction_list.append(
            models.Transaction(
                information=db_transaction_information, account_id=account_id
            )
        )

    session.add_all(transaction_list)
    session.commit()
