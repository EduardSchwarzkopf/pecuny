import jwt
import pytest
from httpx import Cookies
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app import models, schemas
from app.auth_manager import get_strategy
from app.config import settings
from app.repository import Repository
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

ENDPOINT = "/api/auth"


@pytest.mark.parametrize(
    "username, displayname, password",
    [
        ("john@pytest.de", "John", "password123"),
        ("random-name@pytest.de", "", "password123"),
    ],
)
async def test_create_user(
    username: str,
    displayname: str,
    password: str,
    repository: Repository,
):
    """
    Test case for creating a user.

    Args:
        username (str): The username of the user.
        displayname (str): The display name of the user.
        password (str): The password of the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        f"{ENDPOINT}/register",
        json={
            "email": username,
            "password": password,
            "displayname": displayname,
        },
    )
    assert res.status_code == HTTP_201_CREATED

    new_user = schemas.UserRead(**res.json())

    db_user = await repository.get(models.User, new_user.id)

    assert db_user is not None

    assert new_user.email == username
    assert new_user.displayname != ""
    assert new_user.is_active is True
    assert new_user.is_superuser is False
    assert new_user.is_verified is False

    assert db_user.hashed_password != password
    assert db_user.email == username.lower()
    assert new_user.email == db_user.email
    assert new_user.displayname == db_user.displayname
    assert new_user.is_active is db_user.is_active
    assert new_user.is_superuser is db_user.is_superuser
    assert new_user.is_verified is db_user.is_verified


async def test_invalid_create_user(test_user: models.User):
    """
    Test case for creating an invalid user.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    email = test_user.email
    res = await make_http_request(
        f"{ENDPOINT}/register",
        json={"email": email, "password": "testpassword", "displayname": "John"},
    )

    assert res.status_code == HTTP_400_BAD_REQUEST


async def test_login_active_user(
    active_user: models.User, common_user_data: schemas.UserCreate
):
    """
    Test case for login.

    Args:
        None

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    for username in [
        "user123@example.com",
        "useR123@example.com",
        "USER123@exAMPLE.com",
        "user123@example.Com",
        "uSeR123@ExAmPlE.COM",
    ]:

        res = await make_http_request(
            f"{ENDPOINT}/login",
            {
                "username": username,
                "password": common_user_data.password,
            },
        )

        token = res.cookies.get(settings.access_token_name)

        payload = jwt.decode(
            token,
            settings.access_token_secret_key,
            algorithms=settings.algorithm,
            audience=settings.token_audience,
        )
        user_id = payload["sub"]

        assert user_id == str(active_user.id)
        assert res.status_code == HTTP_204_NO_CONTENT

        response = await make_http_request(
            "/api/users/me", method=RequestMethod.GET, cookies=res.cookies
        )

        assert response.status_code == HTTP_200_OK


async def test_login_active_verified_user(
    active_verified_user: models.User, common_user_data: schemas.UserCreate
):
    """
    Test case for login.

    Args:
        None

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    for username in [
        "user123@example.com",
        "useR123@example.com",
        "USER123@exAMPLE.com",
        "user123@example.Com",
        "uSeR123@ExAmPlE.COM",
    ]:

        res = await make_http_request(
            f"{ENDPOINT}/login",
            {
                "username": username,
                "password": common_user_data.password,
            },
        )

        token = res.cookies.get(settings.access_token_name)

        payload = jwt.decode(
            token,
            settings.access_token_secret_key,
            algorithms=settings.algorithm,
            audience=settings.token_audience,
        )
        user_id = payload["sub"]

        assert user_id == str(active_verified_user.id)
        assert res.status_code == HTTP_204_NO_CONTENT

        response = await make_http_request(
            "/api/users/me", method=RequestMethod.GET, cookies=res.cookies
        )

        assert response.status_code == HTTP_200_OK


async def test_login_inactive_user(
    inactive_user: models.User, common_user_data: schemas.UserCreate
):
    """
    Test case for logging in with an inactive user.

    Args:
        test_inactive_user: The inactive user attempting to log in.
        common_user_data: Common user data for the login attempt.

    Returns:
        None
    """

    res = await make_http_request(
        f"{ENDPOINT}/login",
        {
            "username": inactive_user.email,
            "password": common_user_data.password,
        },
    )

    assert res.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("wrongemail@gmail.com", "password123", HTTP_400_BAD_REQUEST),
        ("hello123@pytest.de", "wrongPassword", HTTP_400_BAD_REQUEST),
        ("aaaa", "wrongPassword", HTTP_400_BAD_REQUEST),
        ("*39goa", "wrongPassword", HTTP_400_BAD_REQUEST),
        (None, "wrongPassword", HTTP_422_UNPROCESSABLE_ENTITY),
        ("wrongemail@gmail.com", None, HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
async def test_invalid_login_inactive_user(
    username: str,
    password: str,
    status_code: int,
):
    """
    Test case for invalid login.

    Args:
        username (str): The username for the login.
        password (str): The password for the login.
        status_code (int): The expected status code of the response.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    res = await make_http_request(
        f"{ENDPOINT}/login",
        {"username": username, "password": password},
    )

    assert res.status_code == status_code


async def test_logout(test_user: models.User):
    """
    Test the API endpoint for user logout.

    Args:
        test_user: The test user object for simulating the logout.

    Returns:
        None
    """

    res = await make_http_request(url="/api/auth/logout", as_user=test_user)

    # TODO: check for other states as well
    assert res.status_code == HTTP_204_NO_CONTENT


async def test_refresh_token_handling(test_user: models.User):
    """
    Test function to verify the handling of refreshing tokens for a given test user.

    Args:
        test_user: The test user object for token refresh testing.

    Returns:
        None
    """

    strategy = get_strategy()
    token = await strategy.write_refresh_token(test_user)

    cookies = Cookies(
        {
            settings.refresh_token_name: token,
        }
    )

    endpoint = "/api/users/me"

    res = await make_http_request(
        url=endpoint, method=RequestMethod.GET, cookies=cookies
    )
    assert res.status_code == HTTP_200_OK
