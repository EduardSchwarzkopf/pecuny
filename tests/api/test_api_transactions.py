from decimal import Decimal

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from app import models, schemas
from app.date_manager import get_iso_timestring
from app.repository import Repository
from app.utils.classes import RoundedDecimal
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_user_offset_wallet, make_http_request

ENDPOINT = "/api/transactions/"

# pylint: disable=duplicate-code


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
    test_wallet: models.Wallet,
    test_user: models.User,
):
    """
    Test case for creating a transaction.

    Args:
        amount (float | int): The amount of the transaction.
        reference (str): The reference of the transaction.
        category_id (int): The category ID of the transaction.
        test_wallet (models.Wallet): The test wallet.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """
    wallet_balance = test_wallet.balance

    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": test_wallet.id,
            "amount": amount,
            "reference": reference,
            "date": get_iso_timestring(),
            "category_id": category_id,
        },
        as_user=test_user,
    )

    json_response = res.json()
    new_transaction = schemas.Transaction(**json_response)

    assert res.status_code == HTTP_201_CREATED
    assert wallet_balance + Decimal(amount) == test_wallet.balance
    assert new_transaction.wallet_id == test_wallet.id
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
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
):
    """
    Test case for updating a transaction.

    Args:
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.
        test_wallet (models.Wallet): The test wallet.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    reference = f"Updated Val {amount}"

    json = {
        "wallet_id": test_wallet.id,
        "amount": amount,
        "reference": f"Updated Val {amount}",
        "date": get_iso_timestring(),
        "category_id": category_id,
    }

    wallet_balance = test_wallet.balance

    transaction_list = await repository.filter_by(
        models.Transaction, models.Transaction.wallet_id, test_wallet.id
    )

    transaction = transaction_list[0]

    transaction_amount_before = transaction.information.amount

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}", json=json, as_user=test_user
    )

    assert res.status_code == HTTP_200_OK

    transaction = schemas.Transaction(**res.json())

    assert transaction is not None

    updated_test_wallet = await repository.get(models.Wallet, test_wallet.id)

    assert updated_test_wallet is not None

    amount = RoundedDecimal(amount)
    difference = RoundedDecimal(transaction_amount_before - amount)

    assert updated_test_wallet.balance == wallet_balance - difference
    assert transaction.information.amount == amount
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


async def test_delete_transactions(
    test_wallet: models.Wallet,
    test_wallet_transaction_list: list[models.Transaction],
    test_user: models.User,
    repository: Repository,
):
    """
    Test case for deleting transactions.

    Args:
        test_wallet (fixture): The test wallet.
        test_wallet_transaction_list (fixture): The list of test wallet transactions.
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    for transaction in test_wallet_transaction_list:

        wallet_balance = test_wallet.balance
        amount = transaction.information.amount
        transaction_id = transaction.id

        res = await make_http_request(
            f"{ENDPOINT}{transaction_id}",
            method=RequestMethod.DELETE,
            as_user=test_user,
        )
        assert res.status_code == HTTP_204_NO_CONTENT
        result = await repository.get(models.Transaction, transaction_id)

        assert result is None

        wallet = await repository.get(models.Wallet, test_wallet.id)

        assert wallet is not None

        wallet_balance_after = wallet.balance

        expected_balance = wallet_balance - amount
        assert wallet_balance_after == expected_balance

        assert await repository.get(models.Transaction, transaction_id) is None


@pytest.mark.usefixtures("create_transactions")
async def test_delete_transactions_fail(test_user: models.User, repository: Repository):
    """
    Test case for failing to delete transactions.

    Args:
        test_wallet (models.Wallet): The test wallet.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    wallet = await get_other_user_wallet(test_user, repository)
    transaction = await repository.filter_by(
        models.Transaction,
        models.Transaction.wallet_id,
        wallet.id,
    )

    transaction = transaction[0]

    wallet_id = wallet.id
    wallet_balance = wallet.balance

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}",
        method=RequestMethod.DELETE,
        as_user=test_user,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED

    wallet_refresh = await repository.get(models.Wallet, wallet_id)

    assert wallet_refresh is not None

    wallet_balance_after = wallet_refresh.balance

    assert wallet_balance_after == wallet_balance


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
    test_wallet: models.Wallet,
    test_user: models.User,
    amount: int | float,
    expected_offset_amount: int | float,
    category_id,
    repository: Repository,
):
    """
    Test case for creating an offset transaction.

    Args:
        test_wallet (models.Wallet): The test wallet.
        test_user (models.User): The test user.
        amount (int | float): The amount of the transaction.
        expected_offset_amount (int | float): The expected amount of the offset transaction.
        category_id (int): The category ID of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    wallet_id = test_wallet.id
    offset_wallet = await get_user_offset_wallet(test_wallet, repository)

    assert offset_wallet is not None

    reference = f"test_create_offset_transaction - {amount}"
    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": wallet_id,
            "amount": amount,
            "reference": reference,
            "date": get_iso_timestring(),
            "category_id": category_id,
            "offset_wallet_id": offset_wallet.id,
        },
        as_user=test_user,
    )

    assert res.status_code == HTTP_201_CREATED

    new_transaction = schemas.Transaction(**res.json())
    offset_transactions_id = new_transaction.offset_transactions_id

    assert isinstance(offset_transactions_id, int)

    new_offset_transaction = await repository.get(
        models.Transaction, offset_transactions_id
    )

    assert new_offset_transaction is not None

    assert new_transaction.wallet_id == wallet_id
    assert new_offset_transaction.wallet_id == offset_wallet.id

    assert new_transaction.information.amount == round(amount, 2)
    assert new_offset_transaction.information.amount == round(expected_offset_amount, 2)

    assert isinstance(new_transaction.information.amount, Decimal)
    assert isinstance(new_offset_transaction.information.amount, Decimal)

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


async def test_create_offset_transaction_other_wallet_fail(
    test_wallet: models.Wallet, test_user: models.User, repository: Repository
):
    """
    Test case for failing to create an offset transaction with another wallet.

    Args:
        test_wallet (models.Wallet): The test wallet.
        test_wallets (list[models.Wallet]): The list of test wallets.
        test_user (models.User): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
        ValueError: If no offset wallet is found.

    """

    offset_wallet_list = await repository.filter_by(
        models.Wallet,
        models.Wallet.user_id,
        test_user.id,
        DatabaseFilterOperator.NOT_EQUAL,
    )

    if offset_wallet_list is None:
        raise ValueError("No offset wallet found")

    offset_wallet = offset_wallet_list[0]

    wallet_balance = test_wallet.balance
    offset_wallet_balance = offset_wallet.balance
    wallet_id = test_wallet.id
    offset_wallet_id = offset_wallet.id

    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": wallet_id,
            "amount": 42,
            "reference": "Not allowed",
            "date": get_iso_timestring(),
            "category_id": 1,
            "offset_wallet_id": offset_wallet_id,
        },
        as_user=test_user,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED

    wallet_refreshed = await repository.get(models.Wallet, wallet_id)
    offset_wallet_refreshed = await repository.get(models.Wallet, offset_wallet_id)

    assert wallet_refreshed is not None
    assert offset_wallet_refreshed is not None

    assert wallet_balance == wallet_refreshed.balance
    assert offset_wallet_balance == offset_wallet_refreshed.balance


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
    test_wallet: models.Wallet,
    category_id: int,
    amount: int | float | RoundedDecimal,
    repository: Repository,
):
    """
    Test case for updating an offset transaction.

    Args:
        test_wallet (models.Wallet): The test wallet.
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    offset_wallet = await get_user_offset_wallet(test_wallet, repository)

    assert offset_wallet is not None

    wallet_balance = test_wallet.balance
    offset_wallet_balance = offset_wallet.balance
    wallet_id = test_wallet.id
    offset_wallet_id = offset_wallet.id

    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": wallet_id,
            "amount": 5,
            "reference": "creation",
            "date": get_iso_timestring(),
            "category_id": category_id,
            "offset_wallet_id": offset_wallet_id,
        },
        as_user=test_wallet.user,
    )

    transaction_before = schemas.Transaction(**transaction_res.json())

    reference = f"Offset_transaction with {amount}"
    res = await make_http_request(
        f"{ENDPOINT}{transaction_before.id}",
        json={
            "wallet_id": wallet_id,
            "amount": amount,
            "reference": reference,
            "date": get_iso_timestring(),
            "category_id": category_id,
        },
        as_user=test_wallet.user,
    )

    assert res.status_code == HTTP_200_OK

    transaction = schemas.Transaction(**res.json())

    amount = RoundedDecimal(amount)
    assert transaction.information.amount == amount

    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id

    wallet_refreshed = await repository.get(models.Wallet, wallet_id)
    offset_wallet_refreshed = await repository.get(models.Wallet, offset_wallet_id)

    assert wallet_refreshed is not None
    assert offset_wallet_refreshed is not None

    assert wallet_refreshed.balance == wallet_balance + amount
    assert offset_wallet_refreshed.balance == offset_wallet_balance - amount


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
    test_wallet: models.Wallet,
    test_user: models.User,
    category_id: int,
    amount: int | float,
    repository: Repository,
):
    """
    Test case for deleting an offset transaction.

    Args:
        test_wallet (models.Wallet): The test wallet.
        test_user (models.User): The test user.
        category_id (int): The category ID of the transaction.
        amount (int | float): The amount of the transaction.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    offset_wallet = await get_user_offset_wallet(test_wallet, repository)

    assert offset_wallet is not None

    wallet_balance = test_wallet.balance
    offset_wallet_balance = offset_wallet.balance

    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": test_wallet.id,
            "amount": amount,
            "reference": "creation",
            "date": get_iso_timestring(),
            "category_id": category_id,
            "offset_wallet_id": offset_wallet.id,
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

    assert res.status_code == HTTP_204_NO_CONTENT
    assert offset_transaction_res.status_code == HTTP_404_NOT_FOUND

    wallet_refresh = await repository.get(models.Wallet, test_wallet.id)
    offset_wallet_refresh = await repository.get(models.Wallet, offset_wallet.id)

    assert wallet_refresh is not None
    assert offset_wallet_refresh is not None

    assert offset_wallet_balance == offset_wallet_refresh.balance
    assert wallet_balance == wallet_refresh.balance


async def test_transaction_amount_is_number(
    test_wallet_transaction_list: list[models.Transaction], repository: Repository
):
    """
    Tests if the transaction amount in the JSON response is a float.

    Args:
        test_wallet_transaction_list (fixture): The list of wallet transactions.
        test_user (fixture): The test user.
    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    transaction = test_wallet_transaction_list[0]
    wallet = await repository.get(
        models.Wallet, transaction.wallet_id, [models.Wallet.user]
    )

    assert wallet is not None

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}",
        as_user=wallet.user,
        method=RequestMethod.GET,
    )

    json_response = res.json()

    assert isinstance(json_response["information"]["amount"], float)
