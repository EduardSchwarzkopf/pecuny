import pytest
from jose import jwt

from app import models
from app import repository as repo
from app import schemas
from app.config import settings
from tests.fixtures import ClientSessionWrapper

pytestmark = pytest.mark.anyio
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
    client_session_wrapper: ClientSessionWrapper,
    username,
    displayname,
    password,
):
    """
    Tests the create user functionality.

    Args:
        session: The session fixture.
        client: The async client fixture.
        username (str): The username of the user to create.
        displayname (str): The display name of the user to create.
        password (str): The password of the user to create.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.client.post(
            f"{ENDPOINT}/register",
            json={
                "email": username,
                "password": password,
                "displayname": displayname,
            },
        )
    assert res.status_code == 201

    new_user = schemas.UserRead(**res.json())

    assert new_user.email == username
    assert new_user.displayname != ""
    assert new_user.is_active is True
    assert new_user.is_superuser is False
    assert new_user.is_verified is False


@pytest.mark.usefixtures("test_user")
async def test_invalid_create_user(
    client_session_wrapper: ClientSessionWrapper,
):
    """
    Tests the invalid user creation.

    Args:
        session: The session fixture.
        client: The async client fixture.
        username (str): The username of the user to create.
        displayname (str): The display name of the user to create.
        password (str): The password of the user to create.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.client.post(
            f"{ENDPOINT}/register",
            json={
                "email": "hello123@pytest.de",
                "password": "testpassword",
                "displayname": "John",
            },
        )

    assert res.status_code == 400


@pytest.mark.parametrize(
    "username, displayname, password",
    [
        ("hello123@pytest.de", "John", "password123"),
        ("hellO123@pytest.de", "John", "password123"),
        ("HELLO123@pytest.de", "John", "password123"),
        ("hello123@PyTeSt.De", "John", "password123"),
        ("hELLO123@pytest.de", "John", "password123"),
    ],
)
async def test_login(
    client_session_wrapper: ClientSessionWrapper,
    test_user,
    username,
    displayname,
    password,
):
    """
    Tests successful user login

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.client.post(
            f"{ENDPOINT}/login",
            data={
                "username": username,
                "displayname": displayname,
                "password": password,
            },
        )

    cookie = res.cookies.get("fastapiusersauth")
    payload = jwt.decode(
        cookie,
        settings.secret_key,
        algorithms=settings.algorithm,
        audience="fastapi-users:auth",
    )
    user_id = payload["sub"]

    assert user_id == str(test_user.id)
    assert res.status_code == SUCCESS_LOGIN_STATUS_CODE


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
    client_session_wrapper: ClientSessionWrapper,
    username,
    password,
    status_code,
):
    """
    Tests failed user login.

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.client.post(
            f"{ENDPOINT}/login", data={"username": username, "password": password}
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
@pytest.mark.usefixtures("test_user")
async def test_updated_user(client_session_wrapper: ClientSessionWrapper, values):
    """
    Tests successful update user parameter.

    Args:
        session: The session fixture.
        client: The async client fixture.
        username (str): The username of the user to create.
        displayname (str): The display name of the user to create.
        password (str): The password of the user to create.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.patch(
            "/api/users/me", json=values
        )

        assert res.status_code == 200
        user = schemas.UserRead(**res.json())

        for key, value in values.items():
            if key == "password":
                login_res = await client_session_wrapper.authorized_client.post(
                    f"{ENDPOINT}/login",
                    data={"username": user.email, "password": value},
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
async def test_invalid_updated_user(
    client_session_wrapper: ClientSessionWrapper, test_user, values
):
    """
    Tests tests invalid update user functionality.

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    user_id = str(test_user.id)
    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.patch(
            f"/api/users/{user_id}", json=values
        )

    assert res.status_code == 403


@pytest.mark.usefixtures("client")
async def test_delete_user(client_session_wrapper: ClientSessionWrapper, test_user):
    """
    Tests the create user functionality.

    Args:
        session: The session fixture.
        client: The async client fixture.
        username (str): The username of the user to create.
        displayname (str): The display name of the user to create.
        password (str): The password of the user to create.

    Returns:
        None
    """
    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.delete("/api/users/me")

        assert res.status_code == 204

        user = await repo.get(models.User, test_user.id)

    assert user is None


async def test_invalid_delete_user(
    client_session_wrapper: ClientSessionWrapper,
):
    """
    Tests invalid user deletion.

    Args:
        session: The session fixture.
        client: The async client fixture.
        username (str): The username of the user to create.
        displayname (str): The display name of the user to create.
        password (str): The password of the user to create.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.delete("/api/users/2")

    assert res.status_code == 403
