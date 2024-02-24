import pytest
from httpx import AsyncClient
from jose import jwt

from app import models
from app import repository as repo
from app import schemas
from app.config import settings

#
# use with: pytest --disable-warnings -v -x
#

pytestmark = pytest.mark.anyio
success_login_status_code = 204
endpoint = "/api/auth"


@pytest.mark.parametrize(
    "username, displayname, password",
    [
        ("john@pytest.de", "John", "password123"),
        ("random-name@pytest.de", "", "password123"),
    ],
)
async def test_create_user(
    session, client: AsyncClient, username, displayname, password
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

    async with session:
        res = await client.post(
            f"{endpoint}/register",
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
    assert new_user.is_active == True
    assert new_user.is_superuser == False
    assert new_user.is_verified == False


@pytest.mark.usefixtures("test_user")
async def test_invalid_create_user(session, client: AsyncClient):
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

    async with session:
        res = await client.post(
            f"{endpoint}/register",
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
    session, client: AsyncClient, test_user, username, displayname, password
):
    """
    Tests the delete user functionality.

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    async with session:
        res = await client.post(
            f"{endpoint}/login",
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
    assert res.status_code == success_login_status_code


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
    session, client: AsyncClient, username, password, status_code
):
    """
    Tests the delete user functionality.

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    async with session:
        res = await client.post(
            f"{endpoint}/login", data={"username": username, "password": password}
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
async def test_updated_user(session, authorized_client: AsyncClient, values):
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

    async with session:
        res = await authorized_client.patch("/api/users/me", json=values)

        assert res.status_code == 200
        user = schemas.UserRead(**res.json())

        for key, value in values.items():
            if key == "password":
                login_res = await authorized_client.post(
                    f"{endpoint}/login",
                    data={"username": user.email, "password": value},
                )
                assert login_res.status_code == success_login_status_code
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
    session, authorized_client: AsyncClient, test_user, values
):
    """
    Tests the delete user functionality.

    Args:
        authorized_client: The authorized client fixture.
        session: The session fixture.

    Returns:
        None
    """

    id = str(test_user.id)
    async with session:
        res = await authorized_client.patch(f"/api/users/{id}", json=values)

    assert res.status_code == 403


@pytest.mark.usefixtures("client")
async def test_delete_user(session, test_user, authorized_client):
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
    async with session:
        res = await authorized_client.delete("/api/users/me")

        assert res.status_code == 204

        user = await repo.get(models.User, test_user.id)

    assert user is None


async def test_invalid_delete_user(authorized_client: AsyncClient, session):
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

    async with session:
        res = await authorized_client.delete("/api/users/2")

    assert res.status_code == 403
