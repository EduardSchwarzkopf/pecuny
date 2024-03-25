import jwt
import pytest

from app import models
from app import repository as repo
from app import schemas
from app.config import settings
from app.utils.enums import DatabaseFilterOperator, RequestMethod
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


@pytest.mark.usefixtures("test_users")
async def test_login():
    """
    Test case for login.

    Args:
        None

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    login_user_list = await repo.filter_by(
        models.User, models.User.email, "hello123@pytest.de"
    )
    login_user = login_user_list[0]

    for username in [
        "hello123@pytest.de",
        "hellO123@pytest.de",
        "HELLO123@pytest.de",
        "hello123@PyTeSt.De",
        "hELLO123@pytest.de",
    ]:

        res = await make_http_request(
            f"{ENDPOINT}/login",
            {
                "username": username,
                "password": "password123",
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

        assert user_id == str(login_user.id)
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
async def test_invalid_login(
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


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mew@mew.de"}),
        ({"email": "another@mail.com"}),
        ({"displayname": "Agent Smith"}),
        ({"password": "lancelot"}),
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

        assert getattr(user, key) == value


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mewmew.de"}),
        ({"password": ""}),
        ({"is_superuser": True}),
        ({"email": "anothermail.com"}),
    ],
)
async def test_invalid_updated_user(test_user: models.User, values: dict):
    """
    Test case for updating a user with invalid values.

    Args:
        test_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    user_id = str(test_user.id)
    res = await make_http_request(
        f"/api/users/{user_id}",
        json=values,
        method=RequestMethod.PATCH,
        as_user=test_user,
    )

    assert res.status_code == 403


async def test_delete_user(
    test_user: models.User,
):
    """
    Test case for deleting a user.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    res = await make_http_request(
        "/api/users/me", method=RequestMethod.DELETE, as_user=test_user
    )

    assert res.status_code == 204

    user = await repo.get(models.User, test_user.id)
    assert user is None


async def test_invalid_delete_user(test_user: models.User):
    """
    Test case for deleting a user.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    other_user_list = await repo.filter_by_multiple(
        models.User,
        [
            (models.User.email, test_user.email, DatabaseFilterOperator.NOT_EQUAL),
            (models.User.is_verified, True, DatabaseFilterOperator.EQUAL),
        ],
    )
    other_user = other_user_list[-1]
    res = await make_http_request(
        url=f"/api/users/{other_user.id}",
        method=RequestMethod.DELETE,
        as_user=test_user,
    )

    assert res.status_code == 403
