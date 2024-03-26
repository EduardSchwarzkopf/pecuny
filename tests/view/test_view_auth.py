import jwt
import pytest
from fastapi import Response
from httpx import Cookies

from app import auth_manager, models
from app import repository as repo
from app import schemas
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_create_user():
    pass


async def test_invalid_create_user():
    pass


async def test_updated_user():
    pass


async def test_login():
    pass


async def test_invalid_api_login():
    pass


async def test_logout(test_user: models.User):
    pass
