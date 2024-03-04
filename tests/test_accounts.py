import pytest

from app import models
from app import repository as repo
from app import schemas
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

pytestmark = pytest.mark.anyio
ENDPOINT = "/api/accounts/"

# TODO: Add get account test


async def test_create_account(test_user):
    """
    Tests the create account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.

    Returns:
        None
    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": "test_account", "description": "test", "balance": 500},
        as_user=test_user,
    )

    assert res.status_code == 201

    new_account = schemas.Account(**res.json())

    assert new_account.label == "test_account"
    assert new_account.balance == 500
    assert new_account.description == "test"


@pytest.mark.parametrize(
    "label, description, balance",
    [
        ("", None, None),
        ("test", "test", "aaaa"),
        ("test", "test", "0,3"),
    ],
)
async def test_invalid_create_account(test_user, label, description, balance):
    """
    Tests the delete account functionality.

    Args:
        authorized_client: The authorized client fixture.
        account_id (str): The ID of the account to delete.
        status_code (int): The expected status code.

    Returns:
        None
    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": label, "description": description, "balance": balance},
        as_user=test_user,
    )

    assert res.status_code == 422


async def test_delete_account(test_account):
    """
    Tests the delete account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    user = await repo.get(models.User, test_account.user_id)
    res = await make_http_request(
        f"{ENDPOINT}{test_account.id}",
        as_user=user,
        method=RequestMethod.DELETE,
    )

    assert res.status_code == 204

    account = await repo.get(models.Account, test_account.id)

    assert account is None


async def test_invalid_delete_account(test_user, test_accounts):
    """
    Tests the update account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    status_code = 404

    for account in test_accounts:

        if account.user_id == test_user.id:
            continue

        res = await make_http_request(
            f"{ENDPOINT}{account.id}", as_user=test_user, method=RequestMethod.DELETE
        )

        assert res.status_code == status_code

        account_refresh = await repo.get(models.Account, account.id)

        assert account_refresh == account


@pytest.mark.parametrize(
    "values",
    [
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": 1111.3,
        },
        {
            "label": "11113",
            "description": "cool story bro '",
            "balance": 2000,
        },
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": -0.333333334,
        },
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": -1000000.3,
        },
    ],
)
async def test_update_account(test_account, values):
    """
    Tests the update account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    user = await repo.get(models.User, test_account.user_id)
    response = await make_http_request(
        f"{ENDPOINT}{test_account.id}", json=values, as_user=user
    )

    assert response.status_code == 200
    account = schemas.AccountData(**response.json())

    for key, value in values.items():
        account_val = getattr(account, key)
        print(f"key: {key} | value: {value} | account_val: {account_val}")
        if isinstance(value, str):
            assert account_val == value
        else:
            assert account_val == round(value, 2)
