import pytest
from jose import jwt

from app import schemas
from app.config import settings

#
# use with: pytest --disable-warnings -v -x
#


def test_create_account(authorized_client):
    res = authorized_client.post(
        "/accounts/",
        json={"label": "test_account", "description": "test", "balance": 500},
    )
    new_account = schemas.Account(**res.json())

    assert res.status_code == 201
    assert new_account.label == "test_account"
    assert new_account.balance == 500
    assert new_account.description == "test"


@pytest.mark.parametrize(
    "label, description, balance, status_code",
    [
        ("", None, None, 422),
        ("test", "test", "aaaa", 422),
        ("test", "test", "0,3", 422),
    ],
)
def test_invalid_create_account(
    authorized_client, label, description, balance, status_code
):
    res = authorized_client.post(
        "/accounts/",
        json={"label": label, "description": description, "balance": balance},
    )

    assert res.status_code == status_code
