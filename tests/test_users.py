import pytest
from jose import jwt

from app import schemas
from app.config import settings

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


async def test_invalid_create_user(client, test_user):
    res = await client.post(
        "/auth/register",
        json={"email": "hello123@pytest.de", "password": "testpassword"},
    )

    assert res.status_code == 400


@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("hello123@pytest.de", "password123", 200),
        ("testuser", "password123", 200),
        ("TESTUSER", "password123", 200),
        ("TestUser", "password123", 200),
        ("testUser", "password123", 200),
    ],
)
def test_login(client, test_user, username, password, status_code):
    res = client.post(
        "/login",
        data={"username": username, "password": password},
    )

    login_res = schemas.Token(**res.json())
    payload = jwt.decode(
        login_res.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    id = payload["user_id"]

    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert res.status_code == status_code


@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("wrongemail@gmail.com", "password123", 403),
        ("hello123@pytest.de", "wrongPassword", 403),
        ("aaaa", "wrongPassword", 403),
        ("*39goa", "wrongPassword", 403),
        (None, "wrongPassword", 422),
        ("wrongemail@gmail.com", None, 422),
    ],
)
def test_invalid_login(client, test_user, username, password, status_code):
    res = client.post("/login", data={"username": username, "password": password})

    assert res.status_code == status_code


@pytest.mark.parametrize(
    "values, status_code",
    [
        ({"username": "neuernutzer"}, 200),
        ({"email": "mew@mew.de"}, 200),
        ({"password": "newpassword"}, 200),
        (
            {
                "email": "another@mail.com",
                "username": "next_username",
                "password": "password456",
            },
            200,
        ),
    ],
)
def test_updated_user(authorized_client, test_user, values, status_code):
    res = authorized_client.put("/users/1", json=values)

    assert res.status_code == status_code
    user = schemas.UserData(**res.json())

    for key, value in values.items():
        if key == "password":
            login_res = authorized_client.post(
                "/login", data={"username": user.username, "password": value}
            )
            assert login_res.status_code == 200
            continue

        assert getattr(user, key) == value


@pytest.mark.parametrize(
    "values, status_code",
    [
        ({"username": "%§$"}, 422),
        ({"email": "mewmew.de"}, 422),
        ({"password": ""}, 400),
        (
            {
                "email": "anothermail.com",
                "username": "%=§",
            },
            422,
        ),
    ],
)
def test_invalid_updated_user(authorized_client, test_user, values, status_code):
    res = authorized_client.put("/users/1", json=values)

    assert res.status_code == status_code


def test_delete_user(authorized_client):
    res = authorized_client.delete("/users/1")

    assert res.status_code == 204


def test_invalid_delete_user(authorized_client, session):
    res = authorized_client.delete("/users/2")

    assert res.status_code == 403
