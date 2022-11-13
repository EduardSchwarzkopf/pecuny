import pytest
from jose import jwt

from app import schemas
from app.config import settings

#
# use with: pytest --disable-warnings -v -x
#

pytestmark = pytest.mark.anyio


async def test_create_account(authorized_client):
    res = await authorized_client.post(
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
async def test_invalid_create_account(
    authorized_client, label, description, balance, status_code
):
    res = await authorized_client.post(
        "/accounts/",
        json={"label": label, "description": description, "balance": balance},
    )

    assert res.status_code == status_code


async def test_delete_account(authorized_client, test_account):
    res = await authorized_client.delete("/accounts/1")

    assert res.status_code == 204


@pytest.mark.parametrize(
    "account_id, status_code",
    [("2", 404), ("3", 404), ("4", 404), ("999999", 404)],
)
async def test_invalid_delete_account(
    authorized_client, test_accounts, account_id, status_code
):
    res = await authorized_client.delete(f"/accounts/{account_id}")

    assert res.status_code == status_code


@pytest.mark.parametrize(
    "values, status_code",
    [
        ({"label": "new_label"}, 200),
        ({"description": "my new description"}, 200),
        ({"balance": 1234}, 200),
        (
            {
                "label": "My new Label",
                "description": "very new description",
                "balance": 1111.3,
            },
            200,
        ),
    ],
)
async def test_update_account(authorized_client, test_account, values, status_code):
    res = await authorized_client.put("/accounts/1", json=values)

    assert res.status_code == 200

    account = schemas.AccountData(**res.json())

    for key, value in values.items():
        if key == "id":
            continue

        account_val = getattr(account, key)
        print(f"key: {key} | value: {value} | account_val: {account_val}")
        assert account_val == value
