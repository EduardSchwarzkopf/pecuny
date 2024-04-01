import jwt
import pytest
from httpx import Cookies

from app import models
from app import repository as repo
from app import schemas
from app.auth_manager import get_strategy
from app.config import settings
from app.utils.enums import RequestMethod
from tests.fixtures import UserData
from tests.utils import make_http_request

SUCCESS_LOGIN_STATUS_CODE = 204
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
    assert res.status_code == 201

    new_user = schemas.UserRead(**res.json())

    db_user = await repo.get(models.User, new_user.id)

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

    assert res.status_code == 400


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mew@mew.de"}),
        ({"displayname": "Agent Smith"}),
        ({"password": "lancelot"}),
        (
            {
                "displayname": "Agent Test",
                "email": "user@example.com",
                "password": "password123",
            }
        ),
    ],
)
async def test_updated_user(test_user: models.User, values: dict):
    """
    Test case for updating a user.

    Args:
        test_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    res = await make_http_request(
        "/api/users/me", json=values, method=RequestMethod.PATCH, as_user=test_user
    )

    assert res.status_code == 200
    user = schemas.UserRead(**res.json())

    for key, value in values.items():
        if key == "password":
            login_res = await make_http_request(
                f"{ENDPOINT}/login",
                {"username": user.email, "password": value},
            )
            assert login_res.status_code == SUCCESS_LOGIN_STATUS_CODE
            continue

        if key == "email":
            db_user: models.User = await repo.get(models.User, test_user.id)
            assert db_user.is_verified == False

        assert getattr(user, key) == value


async def test_login_active_user(test_active_user):
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
                "password": UserData.password,
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

        assert user_id == str(test_active_user.id)
        assert res.status_code == SUCCESS_LOGIN_STATUS_CODE

        response = await make_http_request(
            "/api/users/me", method=RequestMethod.GET, cookies=res.cookies
        )

        assert response.status_code == 200


async def test_login_active_verified_user(test_active_verified_user):
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
                "password": UserData.password,
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

        assert user_id == str(test_active_verified_user.id)
        assert res.status_code == SUCCESS_LOGIN_STATUS_CODE

        response = await make_http_request(
            "/api/users/me", method=RequestMethod.GET, cookies=res.cookies
        )

        assert response.status_code == 200


@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("wrongemail@gmail.com", "password123", 400),
        ("hello123@pytest.de", "wrongPassword", 400),
        ("aaaa", "wrongPassword", 400),
        ("*39goa", "wrongPassword", 400),
        (None, "wrongPassword", 422),
        ("wrongemail@gmail.com", None, 422),
    ],
)
@pytest.mark.usefixtures("test_user")
async def test_invalid_api_login(
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
    assert res.status_code == 204


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
    assert res.status_code == 200
