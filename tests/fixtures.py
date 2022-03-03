import pytest
import datetime
from fastapi_sqlalchemy import db
from app.oauth2 import create_access_token
from app import models


@pytest.fixture()
def test_user(client):
    user_data = {
        "username": "testuser",
        "email": "hello123@pytest.de",
        "password": "password123",
    }

    res = client.post("/users/", json=user_data)

    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    yield new_user


@pytest.fixture()
def token(test_user):
    yield create_access_token({"user_id": test_user["id"]})


@pytest.fixture()
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": "Bearer " + token}

    yield client


@pytest.fixture()
def test_users():
    users_data = [
        {
            "username": "user01",
            "email": "user01@pytest.de",
            "password": "password123",
        },
        {
            "username": "user02",
            "email": "user02@pytest.de",
            "password": "password123",
        },
        {
            "username": "user03",
            "email": "user03@pytest.de",
            "password": "password123",
        },
    ]

    def create_users_model(user):
        return models.User(**user)

    users_map = map(create_users_model, users_data)
    users = list(users_map)

    with db():
        db.session.add_all(users)

        db.session.commit()
        yield db.session.query(models.User).all()


@pytest.fixture()
def test_account(authorized_client):
    account_data = {"label": "test_account", "description": "test", "balance": 5000}

    res = authorized_client.post("/accounts/", json=account_data)

    assert res.status_code == 201
    new_account = res.json()
    yield new_account


@pytest.fixture()
def test_accounts(test_users):
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

    def create_accounts_model(account):
        return models.Account(**account)

    accounts_map = map(create_accounts_model, accounts_data)
    accounts = list(accounts_map)

    with db():
        db.session.add_all(accounts)

        db.session.commit()
        yield db.session.query(models.Account).all()


def get_date_range(date_start, days=5):
    return [
        (date_start - datetime.timedelta(days=idx)).isoformat() for idx in range(days)
    ]


@pytest.fixture()
def test_transactions(test_accounts):
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
    with db():

        for transaction_info in transaction_data:

            account_id = transaction_info["account_id"]
            account_index = next(
                (i for i, item in enumerate(test_accounts) if item.id == account_id), -1
            )
            if account_index == -1:
                raise ValueError("No Account found with that Id")

            del transaction_info["account_id"]
            db_transaction_information = models.TransactionInformation(
                **transaction_info
            )

            account_query = db.session.query(models.Account).filter_by(id=account_id)
            new_balance = (
                test_accounts[account_index].balance + db_transaction_information.amount
            )
            account_query.update({"balance": new_balance})

            transaction_list.append(
                models.Transaction(
                    information=db_transaction_information, account_id=account_id
                )
            )

        db.session.add_all(transaction_list)
        db.session.commit()
