import pytest
from jose import jwt

from app import schemas
from app.config import settings

#
# use with: pytest --disable-warnings -v -x
#


def test_create_user(client):
    res = client.post(
        "/users/",
        json={
            "username": "my_username",
            "email": "hello123@pytest.de",
            "password": "password123",
        },
    )
    new_user = schemas.UserData(**res.json())

    assert new_user.email == "hello123@pytest.de"
    assert new_user.username == "my_username"
    assert type(new_user.id) == int
    assert res.status_code == 201


@pytest.mark.parametrize(
    "username, email, message, status_code",
    [
        (
            "testuser",
            "my@email.com",
            "Username already in use",
            409,
        ),
        (
            "new_testuser",
            "hello123@pytest.de",
            "E-Mail address already in use",
            409,
        ),
    ],
)
def test_invalid_create_user(client, test_user, username, email, message, status_code):
    res = client.post(
        "/users/",
        json={"username": username, "email": email, "password": "testpassword"},
    )

    res_json = res.json()
    assert res.status_code == status_code
    assert res_json["detail"] == message


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
def test_valid_login(client, test_user, username, password, status_code):
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
