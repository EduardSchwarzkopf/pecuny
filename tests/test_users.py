import pytest
from jose import jwt

from app import schemas, repository as repo, models
from app.config import settings
from httpx import AsyncClient

#
# use with: pytest --disable-warnings -v -x
#

pytestmark = pytest.mark.anyio


@pytest.mark.anyio
async def test_create_user(client):
    res = await client.post(
        "/auth/register",
        json={
            "email": "hello123@pytest.de",
            "password": "password123",
        },
    )
    assert res.status_code == 201

    new_user = schemas.UserRead(**res.json())

    assert new_user.email == "hello123@pytest.de"
    assert new_user.is_active == True
    assert new_user.is_superuser == False
    assert new_user.is_verified == False


async def test_invalid_create_user(session, client: AsyncClient, test_user):
    async with session:
        res = await client.post(
            "/auth/register",
            json={"email": "hello123@pytest.de", "password": "testpassword"},
        )

    assert res.status_code == 400


@pytest.mark.parametrize(
    "username, password",
    [
        ("hello123@pytest.de", "password123"),
        ("hellO123@pytest.de", "password123"),
        ("HELLO123@pytest.de", "password123"),
        ("hello123@PyTeSt.De", "password123"),
        ("hELLO123@pytest.de", "password123"),
    ],
)
async def test_login(session, client: AsyncClient, test_user, username, password):
    async with session:
        res = await client.post(
            "/auth/jwt/login",
            data={"username": username, "password": password},
        )

    login_res = schemas.Token(**res.json())
    payload = jwt.decode(
        login_res.access_token,
        settings.secret_key,
        algorithms=settings.algorithm,
        audience="fastapi-users:auth",
    )
    id = payload["user_id"]

    assert id == str(test_user.id)
    assert login_res.token_type == "bearer"
    assert res.status_code == 200


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
async def test_invalid_login(
    session, client: AsyncClient, test_user, username, password, status_code
):
    async with session:
        res = await client.post(
            "/auth/jwt/login", data={"username": username, "password": password}
        )

    assert res.status_code == status_code


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mew@mew.de"}),
        ({"email": "another@mail.com"}),
        ({"password": "lancelot"}),
    ],
)
async def test_updated_user(session, authorized_client: AsyncClient, test_user, values):
    async with session:
        res = await authorized_client.patch("/users/me", json=values)

    assert res.status_code == 200
    user = schemas.UserRead(**res.json())

    for key, value in values.items():
        if key == "password":
            login_res = await authorized_client.post(
                "/auth/jwt/login", data={"username": user.email, "password": value}
            )
            assert login_res.status_code == 200
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
    id = str(test_user.id)
    async with session:
        res = await authorized_client.patch(f"/users/{id}", json=values)

    assert res.status_code == 403


async def test_delete_user(session, client, test_user, authorized_client):
    async with session:
        res = await authorized_client.delete(f"/users/me")

        assert res.status_code == 204

        user = await repo.get(models.User, test_user.id)

    assert user == None


async def test_invalid_delete_user(authorized_client: AsyncClient, session):
    async with session:
        res = await authorized_client.delete("/users/2")

    assert res.status_code == 403
