from typing import Any, List

import pytest

from app import models
from app import repository as repo
from app import schemas
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

pytestmark = pytest.mark.anyio
ENDPOINT = "/api/accounts/"

# TODO: Add get account test


async def test_create_account(test_user: models.User):
    """
    Test case for creating an account.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

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
        ("test", "test", "aaaa"),
        ("test", None, "0,3"),
        ("test", "", False),
    ],
)
async def test_optional_fields_create_account(
    test_user: models.User, label: str, description: str, balance: int | float
):
    """
    Test case for creating an account with optional fields.

    Args:
        test_user (fixture): The test user.
        label (str): The label of the account.
        description (str): The description of the account.
        balance (int | float): The balance of the account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": label, "description": description, "balance": balance},
        as_user=test_user,
    )

    assert res.status_code == 201


@pytest.mark.parametrize(
    "label",
    [
        (""),
        (None),
        (True),
    ],
)
async def test_invalid_title_create_account(test_user: models.User, label: Any):
    """
    Test case for creating an account with an invalid label.

    Args:
        test_user (fixture): The test user.
        label (Any): The label of the account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": label, "description": "test_invalid_title", "balance": 0},
        as_user=test_user,
    )

    assert res.status_code == 422


async def test_delete_account(test_account: models.Account):
    """
    Test case for deleting an account.

    Args:
        test_account (fixture): The test account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        f"{ENDPOINT}{test_account.id}",
        as_user=test_account.user,
        method=RequestMethod.DELETE,
    )

    assert res.status_code == 204

    account = await repo.get(models.Account, test_account.id)

    assert account is None


async def test_invalid_delete_account(
    test_user: models.User, test_accounts: List[models.Account]
):
    """
    Test case for deleting an account.

    Args:
        test_user (fixture): The test user.
        test_accounts (fixture): The list of test accounts.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

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
async def test_update_account(
    test_account: models.Account, test_user: models.User, values: dict
):
    """
    Test case for updating an account.

    Args:
        test_account (fixture): The test account.
        test_user (fixture): The test user.
        values (dict): The updated values for the account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """
    response = await make_http_request(
        f"{ENDPOINT}{test_account.id}", json=values, as_user=test_user
    )

    assert response.status_code == 200
    account = schemas.AccountData(**response.json())

    db_account = await repo.get(models.Account, account.id)
    for key, value in values.items():
        account_val = getattr(account, key)
        db_account_val = getattr(db_account, key)
        print(f"key: {key} | value: {value} | account_val: {account_val}")
        if not isinstance(value, str):
            value = round(value, 2)

        assert db_account_val == value
        assert account_val == value
