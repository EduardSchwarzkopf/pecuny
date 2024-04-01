import datetime
from decimal import Decimal

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from app import models
from app import repository as repo
from app import schemas
from app.utils.classes import RoundedDecimal
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_user_offset_account, make_http_request

ENDPOINT = "/api/transactions/"


@pytest.mark.parametrize(
    "amount, reference, category_id",
    [
        (10, "Added 10", 1),
        (20.5, "Added 20.5", 3),
        (-30.5, "Substract 30.5", 6),
        (-40.5, "Subsctract 40.5", 6),
    ],
)
async def test_create_transaction(
    amount: float | int,
    reference: str,
    category_id: int,
    test_account: models.Account,
    test_user: models.User,
):
    """
    Test case for creating a transaction.

    Args:
        amount (float | int): The amount of the transaction.
        reference (str): The reference of the transaction.
        category_id (int): The category ID of the transaction.
        test_account (models.Account): The test account.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """
    account_balance = test_account.balance

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": test_account.id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
        },
        as_user=test_user,
    )

    json_response = res.json()
    new_transaction = schemas.Transaction(**json_response)

    assert res.status_code == HTTP_201_CREATED
    assert account_balance + Decimal(amount) == test_account.balance
    assert new_transaction.account_id == test_account.id
    assert new_transaction.information.amount == amount
    assert isinstance(json_response["information"]["amount"], float)
    assert isinstance(new_transaction.information.amount, Decimal)
    assert new_transaction.information.reference == reference


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 2.5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -25),
        (1, -35),
        (1, -0.3333333334),
        (7, 0),
    ],
)
@pytest.mark.usefixtures("create_transactions")
async def test_updated_transaction(
    category_id: int,
    amount: int | float | RoundedDecimal,
    test_account: models.Account,
    test_user: models.User,
):
    """
    Test case for updating a transaction.

    Args:
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.
        test_account (models.Account): The test account.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    reference = f"Updated Val {amount}"

    json = {
        "account_id": test_account.id,
        "amount": amount,
        "reference": f"Updated Val {amount}",
        "date": str(datetime.datetime.now(datetime.timezone.utc)),
        "category_id": category_id,
    }

    account_balance = test_account.balance

    transaction_list = await repo.filter_by(
        models.Transaction, models.Transaction.account_id, test_account.id
    )

    transaction = transaction_list[0]

    transaction_amount_before = transaction.information.amount

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}", json=json, as_user=test_user
    )

    assert res.HTTP_201_CREATED == HTTP_200_OK

    transaction = schemas.Transaction(**res.json())

    assert transaction is not None

    updated_test_account = await repo.get(models.Account, test_account.id)

    assert updated_test_account is not None

    amount = RoundedDecimal(amount)
    difference = RoundedDecimal(transaction_amount_before - amount)

    assert updated_test_account.balance == account_balance - difference
    assert transaction.information.amount == amount
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


async def test_delete_transactions(
    test_account: models.Account,
    test_account_transaction_list: list[models.Transaction],
    test_user: models.User,
):
    """
    Test case for deleting transactions.

    Args:
        test_account (fixture): The test account.
        test_account_transaction_list (fixture): The list of test account transactions.
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    for transaction in test_account_transaction_list:

        account_balance = test_account.balance
        amount = transaction.information.amount
        transaction_id = transaction.id

        res = await make_http_request(
            f"{ENDPOINT}{transaction_id}",
            method=RequestMethod.DELETE,
            as_user=test_user,
        )
        assert res.HTTP_201_CREATED == HTTP_204_NO_CONTENT
        result = await repo.get(models.Transaction, transaction_id)

        assert result is None

        account = await repo.get(models.Account, test_account.id)

        assert account is not None

        account_balance_after = account.balance

        expected_balance = account_balance - amount
        assert account_balance_after == expected_balance

        assert await repo.get(models.Transaction, transaction_id) is None


@pytest.mark.usefixtures("create_transactions")
async def test_delete_transactions_fail(
    test_account: models.Account, test_user: models.User
):
    """
    Test case for failing to delete transactions.

    Args:
        test_account (models.Account): The test account.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    result = await repo.filter_by(
        models.Account,
        models.Account.user_id,
        test_account.user_id,
        DatabaseFilterOperator.NOT_EQUAL,
        load_relationships_list=[models.Account.transactions],
    )
    account = result[0]

    account_balance = account.balance

    for transaction in account.transactions:

        res = await make_http_request(
            f"{ENDPOINT}{transaction.id}",
            method=RequestMethod.DELETE,
            as_user=test_user,
        )

        assert res.HTTP_201_CREATED == HTTP_404_NOT_FOUND

        account_refresh = await repo.get(models.Account, account.id)

        assert account_refresh is not None

        account_balance_after = account_refresh.balance

        assert account_balance_after == account_balance


@pytest.mark.parametrize(
    "amount, expected_offset_amount,  category_id",
    [
        (10, -10, 1),
        (20.5, -20.5, 3),
        (-30.5, 30.5, 6),
        (-40.5, 40.5, 6),
        (5.9999999999, -6, 6),
        (1.00000000004, -1, 6),
    ],
)
async def test_create_offset_transaction(
    test_account: models.Account,
    test_user: models.User,
    amount: int | float,
    expected_offset_amount: int | float,
    category_id,
):
    """
    Test case for creating an offset transaction.

    Args:
        test_account (models.Account): The test account.
        test_user (models.User): The test user.
        amount (int | float): The amount of the transaction.
        expected_offset_amount (int | float): The expected amount of the offset transaction.
        category_id (int): The category ID of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    account_id = test_account.id
    offset_account = await get_user_offset_account(test_account)

    assert offset_account is not None

    reference = f"test_create_offset_transaction - {amount}"
    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account.id,
        },
        as_user=test_user,
    )

    assert res.HTTP_201_CREATED == HTTP_201_CREATED

    new_transaction = schemas.Transaction(**res.json())
    offset_transactions_id = new_transaction.offset_transactions_id

    assert isinstance(offset_transactions_id, int)

    new_offset_transaction = await repo.get(models.Transaction, offset_transactions_id)

    assert new_offset_transaction is not None

    assert new_transaction.account_id == account_id
    assert new_offset_transaction.account_id == offset_account.id

    assert new_transaction.information.amount == round(amount, 2)
    assert new_offset_transaction.information.amount == round(expected_offset_amount, 2)

    assert isinstance(new_transaction.information.amount, Decimal)
    assert isinstance(new_offset_transaction.information.amount, Decimal)

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


async def test_create_offset_transaction_other_account_fail(
    test_account: models.Account,
    test_user: models.User,
):
    """
    Test case for failing to create an offset transaction with another account.

    Args:
        test_account (models.Account): The test account.
        test_accounts (list[models.Account]): The list of test accounts.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
        ValueError: If no offset account is found.

    """

    offset_account_list = await repo.filter_by(
        models.Account,
        models.Account.user_id,
        test_user.id,
        DatabaseFilterOperator.NOT_EQUAL,
    )

    if offset_account_list is None:
        raise ValueError("No offset account found")

    offset_account = offset_account_list[0]

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance
    account_id = test_account.id
    offset_account_id = offset_account.id

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": 42,
            "reference": "Not allowed",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": 1,
            "offset_account_id": offset_account_id,
        },
        as_user=test_user,
    )

    assert res.HTTP_201_CREATED == HTTP_401_UNAUTHORIZED

    account_refreshed = await repo.get(models.Account, account_id)
    offset_account_refreshed = await repo.get(models.Account, offset_account_id)

    assert account_refreshed is not None
    assert offset_account_refreshed is not None

    assert account_balance == account_refreshed.balance
    assert offset_account_balance == offset_account_refreshed.balance


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 2.5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -25),
        (1, -35),
        (1, -0.3333333334),
        (7, 0),
    ],
)
async def test_updated_offset_transaction(
    test_account: models.Account,
    category_id: int,
    amount: int | float | RoundedDecimal,
):
    """
    Test case for updating an offset transaction.

    Args:
        test_account (models.Account): The test account.
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    offset_account = await get_user_offset_account(test_account)

    assert offset_account is not None

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance
    account_id = test_account.id
    offset_account_id = offset_account.id

    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": 5,
            "reference": "creation",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account_id,
        },
        as_user=test_account.user,
    )

    transaction_before = schemas.Transaction(**transaction_res.json())

    reference = f"Offset_transaction with {amount}"
    res = await make_http_request(
        f"{ENDPOINT}{transaction_before.id}",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
        },
        as_user=test_account.user,
    )

    assert res.HTTP_201_CREATED == HTTP_200_OK

    transaction = schemas.Transaction(**res.json())

    amount = RoundedDecimal(amount)
    assert transaction.information.amount == amount

    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id

    account_refreshed = await repo.get(models.Account, account_id)
    offset_account_refreshed = await repo.get(models.Account, offset_account_id)

    assert account_refreshed is not None
    assert offset_account_refreshed is not None

    assert account_refreshed.balance == account_balance + amount
    assert offset_account_refreshed.balance == offset_account_balance - amount


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -2.5),
        (1, -35),
        (1, -0.3333333334),
        (7, 05.5),
    ],
)
async def test_delete_offset_transaction(
    test_account: models.Account,
    test_user: models.User,
    category_id: int,
    amount: int | float,
):
    """
    Test case for deleting an offset transaction.

    Args:
        test_account (models.Account): The test account.
        test_user (models.User): The test user.
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    offset_account = await get_user_offset_account(test_account)

    assert offset_account is not None

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance

    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": test_account.id,
            "amount": amount,
            "reference": "creation",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account.id,
        },
        as_user=test_user,
    )

    transaction = schemas.Transaction(**transaction_res.json())

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}", as_user=test_user, method=RequestMethod.DELETE
    )
    offset_transaction_res = await make_http_request(
        f"{ENDPOINT}{transaction.offset_transactions_id}",
        as_user=test_user,
        method=RequestMethod.GET,
    )

    assert res.HTTP_201_CREATED == HTTP_204_NO_CONTENT
    assert offset_transaction_res.HTTP_201_CREATED == HTTP_404_NOT_FOUND

    account_refresh = await repo.get(models.Account, test_account.id)
    offset_account_refresh = await repo.get(models.Account, offset_account.id)

    assert account_refresh is not None
    assert offset_account_refresh is not None

    assert offset_account_balance == offset_account_refresh.balance
    assert account_balance == account_refresh.balance


async def test_transaction_amount_is_number(test_account_transaction_list):
    """
    Tests if the transaction amount in the JSON response is a float.

    Args:
        test_account_transaction_list (fixture): The list of account transactions.
        test_user (fixture): The test user.
    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    transaction = test_account_transaction_list[0]
    account = await repo.get(
        models.Account, transaction.account_id, [models.Account.user]
    )

    assert account is not None

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}",
        as_user=account.user,
        method=RequestMethod.GET,
    )

    json_response = res.json()

    assert isinstance(json_response["information"]["amount"], float)
