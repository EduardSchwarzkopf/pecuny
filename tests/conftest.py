import pytest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db
from app.main import app
from app.config import settings
from app.database import Base
from app.oauth2 import create_access_token
from app import models, events

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_username}:{settings.db_passwort}@{settings.db_host}:{settings.db_port}/{settings.db_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
app.add_middleware(DBSessionMiddleware, db_url=SQLALCHEMY_DATABASE_URL)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with db():
        events.create_categories(db.session)


@pytest.fixture()
def client(session):
    yield TestClient(app)


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
    return new_user


@pytest.fixture()
def token(test_user):
    return create_access_token({"user_id": test_user["id"]})


@pytest.fixture()
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": "Bearer " + token}

    return client


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
        return db.session.query(models.User).all()


@pytest.fixture()
def test_account(authorized_client):
    account_data = {"label": "test_account", "description": "test", "balance": 5000}

    res = authorized_client.post("/accounts/", json=account_data)

    assert res.status_code == 201
    new_account = res.json()
    return new_account


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
        return db.session.query(models.User).all()


def get_date_range(date_start, days=5):
    return [
        (date_start - datetime.timedelta(days=idx)).isoformat() for idx in range(days)
    ]


@pytest.fixture()
def test_transactions(authorized_client, test_accounts):
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
            "account_id": 1,
            "amount": 50,
            "reference": "transaction_003",
            "date": dates[3],
            "subcategory_id": 4,
        },
        {
            "account_id": 5,
            "amount": 100,
            "reference": "transaction_004",
            "date": dates[4],
            "subcategory_id": 8,
        },
        {
            "account_id": 5,
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

    for transaction in transaction_data:
        res = authorized_client.post("/transactions/", json=transaction)
        assert res.status_code == 201
