import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from fastapi_sqlalchemy import DBSessionMiddleware
from app.main import app
from app.config import settings
from app.database import Base
from app.oauth2 import create_access_token

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_username}:{settings.db_passwort}@{settings.db_host}:{settings.db_port}/{settings.db_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
app.add_middleware(DBSessionMiddleware, db_url=SQLALCHEMY_DATABASE_URL)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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
