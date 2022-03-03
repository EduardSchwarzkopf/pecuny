import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db
from app.main import app
from app.config import settings
from app.database import Base
from app import events

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


from .fixtures import *
