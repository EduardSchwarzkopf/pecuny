from decimal import Decimal
from typing import Any, List

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app import models, schemas
from app.date_manager import get_day_delta, get_tomorrow, get_yesterday, now
from app.repository import Repository
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_other_user_wallet, make_http_request

ENDPOINT = "/api/scheduled-transactions/"

# pylint: disable=duplicate-code


@pytest.mark.parametrize(
    "amount, reference, category_id, frequency_id",
    [
        (10, "Added 10", 1, 2),
        (20.5, "Added 20.5", 3, 2),
        (-30.5, "Substract 30.5", 6, 3),
        (-40.5, "Subsctract 40.5", 6, 4),
        (-0.5, "Subsctract .5", 6, 5),
    ],
)
async def test_create_scheduled_transaction(
    amount: float | int,
    reference: str,
    category_id: int,
    frequency_id: int,
    test_wallet: models.Wallet,
    test_user: models.User,
):
    """
    Test creating scheduled transactions with different amounts,
    references, category IDs, and frequency IDs.

    Args:
        amount: The amount of the transaction.
        reference: The reference for the transaction.
        category_id: The category ID of the transaction.
        frequency_id: The frequency ID of the transaction.
        test_wallet (fixture): The wallet for which the transaction is created.
        test_user (fixture): The user creating the transaction.
    """

    yesterday = get_yesterday()
    tomorrow = get_tomorrow()

    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": test_wallet.id,
            "amount": amount,
            "reference": reference,
            "date_start": yesterday.isoformat(),
            "date_end": tomorrow.isoformat(),
            "category_id": category_id,
            "frequency_id": frequency_id,
        },
        as_user=test_user,
    )

    json_response = res.json()
    new_transaction = schemas.ScheduledTransaction(**json_response)

    assert res.status_code == HTTP_201_CREATED
    assert new_transaction.wallet_id == test_wallet.id
    assert new_transaction.information.amount == amount
    assert isinstance(json_response["information"]["amount"], float)
    assert isinstance(new_transaction.information.amount, Decimal)
    assert new_transaction.information.reference == reference
    assert new_transaction.date_start == yesterday
    assert new_transaction.date_end == tomorrow


async def test_read_scheduled_transaction(
    test_wallet: models.Wallet,
    test_user: models.User,
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test reading a scheduled transaction.

    Args:
        test_wallet (fixture): The wallet associated with the transaction.
        test_user (fixture): The user performing the read operation.
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for testing.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), as_user=test_user, method=RequestMethod.GET
    )

    json_response = res.json()
    read_transaction = schemas.ScheduledTransaction(**json_response)

    assert res.status_code == HTTP_200_OK
    assert read_transaction.wallet_id == test_wallet.id
    assert read_transaction.information.amount == transaction.information.amount
    assert read_transaction.information.reference == transaction.information.reference
    assert read_transaction.date_start == transaction.date_start
    assert read_transaction.date_end == transaction.date_end
    assert (
        read_transaction.information.category_id == transaction.information.category_id
    )
    assert read_transaction.frequency.id == transaction.frequency_id


async def test_update_scheduled_transaction(
    test_user: models.User,
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test updating a scheduled transaction with new information.

    Args:
        test_user (fixture): The user performing the update.
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for testing.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    now_ = now()

    reference = "Updated reference"
    amount = 10000
    category_id = 3
    frequency_id = 2
    date_start = get_day_delta(now_, -3)
    date_end = get_day_delta(now_, +3)

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        as_user=test_user,
        json={
            "wallet_id": transaction.wallet_id,
            "amount": amount,
            "reference": reference,
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat(),
            "category_id": category_id,
            "frequency_id": frequency_id,
        },
    )

    assert res.status_code == HTTP_200_OK

    updated_transaction = schemas.ScheduledTransaction(**res.json())

    assert updated_transaction.information.amount == amount
    assert updated_transaction.information.reference == reference
    assert updated_transaction.date_start == date_start
    assert updated_transaction.date_end == date_end
    assert updated_transaction.frequency.id == frequency_id
    assert updated_transaction.information.category_id == category_id


async def test_delete_scheduled_transaction(
    test_user: models.User,
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):
    """
    Test deleting a scheduled transaction.

    Args:
        test_user (fixture): The user performing the deletion.
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for testing.
        repository (fixture): The repository for database operations.
    """

    transaction = test_wallet_scheduled_transaction_list[0]
    transaction_id = transaction.id

    res = await make_http_request(
        ENDPOINT + str(transaction_id), as_user=test_user, method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    db_transaction = await repository.get(models.TransactionScheduled, transaction_id)

    assert db_transaction is None


# Tests for unauthorized access
@pytest.mark.usefixtures("test_wallet_scheduled_transaction_list")
async def test_create_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    """
    Tests unauthorized creation of a scheduled transaction.

    Args:
        test_user (fixture): The unauthorized user attempting the creation.
        repository (fixture): The repository for database operations.

    """

    other_wallet = await get_other_user_wallet(test_user, repository)

    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": other_wallet.id,
            "amount": 999,
            "reference": "unautherized",
            "date_start": now().isoformat(),
            "date_end": get_tomorrow().isoformat(),
            "category_id": 1,
            "frequency_id": 2,
        },
        as_user=test_user,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("test_wallet_scheduled_transaction_list")
async def test_read_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    """
    Test reading a scheduled transaction by an unauthorized user.

    Args:
        test_user (fixture): The unauthorized user attempting the read operation.
        repository (fixture): The repository for database operations.

    """

    other_wallet = await get_other_user_wallet(test_user, repository)
    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.wallet_id,
        other_wallet.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), as_user=test_user, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("test_wallet_scheduled_transaction_list")
async def test_update_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    """
    Test updating a scheduled transaction by an unauthorized user.

    Args:
        test_user (fixture): The unauthorized user attempting the update.
        repository (fixture): The repository for database operations.

    """

    other_wallet = await get_other_user_wallet(test_user, repository)
    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.wallet_id,
        other_wallet.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        json={
            "wallet_id": other_wallet.id,
            "amount": 999,
            "reference": "unautherized",
            "date_start": now().isoformat(),
            "date_end": get_tomorrow().isoformat(),
            "category_id": 1,
            "frequency_id": 2,
        },
        as_user=test_user,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("test_wallet_scheduled_transaction_list")
async def test_delete_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    """
    Test deleting a scheduled transaction by an unauthorized user.

    Args:
        test_user (fixture): The unauthorized user attempting the deletion.
        repository (fixture): The repository for database operations.
    """

    other_wallet = await get_other_user_wallet(test_user, repository)

    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.wallet_id,
        other_wallet.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]
    transaction_id = transaction.id

    res = await make_http_request(
        ENDPOINT + str(transaction_id), as_user=test_user, method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED

    transaction_db = await repository.get(models.TransactionScheduled, transaction_id)

    assert isinstance(transaction_db, models.TransactionScheduled)


# Tests for unauthenticated access
async def test_create_scheduled_transaction_unauthenticated(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test creating a scheduled transaction without authentication.

    Args:
        test_wallet_scheduled_transaction_list (fixture):
            ist of scheduled transactions for testing.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT,
        json={
            "wallet_id": transaction.wallet_id,
            "amount": 999,
            "reference": "unautherized",
            "date_start": now().isoformat(),
            "date_end": get_tomorrow().isoformat(),
            "category_id": 1,
            "frequency_id": 2,
        },
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


async def test_read_scheduled_transaction_unauthenticated(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test reading a scheduled transaction without authentication.

    Args:
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for testing.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), method=RequestMethod.GET
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


async def test_update_scheduled_transaction_unauthenticated(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test updating a scheduled transaction without authentication.

    Args:
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for testing.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        json={
            "wallet_id": transaction.wallet_id,
            "amount": 999,
            "reference": "unautherized",
            "date_start": now().isoformat(),
            "date_end": get_tomorrow().isoformat(),
            "category_id": 1,
            "frequency_id": 2,
        },
        method=RequestMethod.GET,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


async def test_delete_scheduled_transaction_unauthenticated(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
):
    """
    Test deleting a scheduled transaction without authentication.

    Args:
        test_wallet_scheduled_transaction_list(fixture):
            Fixture to get a list of scheduled transactions
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


# Tests for handling non-existent entities
async def test_read_scheduled_transaction_not_found(
    test_user: models.User,
):
    """
    Test reading a scheduled transaction that is not found.

    Args:
        test_user (fixture): The user it should be tested with.
    """

    res = await make_http_request(
        ENDPOINT + str(9999), as_user=test_user, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND


# Additional tests for enhanced functionality
@pytest.mark.parametrize(
    "key_to_remove",
    [
        ("wallet_id"),
        ("amount"),
        ("reference"),
        ("date_start"),
        ("date_end"),
        ("category_id"),
        ("frequency_id"),
    ],
)
async def test_create_scheduled_transaction_with_missing_fields(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
    test_user: models.User,
    key_to_remove: str,
):
    """
    Test creation of scheduled transactions with missing data.

    Args:
        test_wallet_scheduled_transaction_list(fixture):
            Fixture to get a list of scheduled transactions
        test_user (fixture): The user it should be tested with.
        key: The key that should be removed from the payload.
    """

    transaction = test_wallet_scheduled_transaction_list[0]

    payload = {
        "wallet_id": transaction.wallet_id,
        "amount": 999,
        "reference": "unautherized",
        "date_start": now().isoformat(),
        "date_end": get_tomorrow().isoformat(),
        "category_id": 1,
        "frequency_id": 2,
    }

    del payload[key_to_remove]

    res = await make_http_request(
        ENDPOINT,
        json=payload,
        as_user=test_user,
    )

    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "key, value",
    [
        ("wallet_id", "test"),
        ("wallet_id", 3.5),
        ("wallet_id", -1),
        ("amount", "test"),
        ("amount", True),
        ("amount", False),
        ("amount", None),
        ("reference", True),
        ("reference", False),
        ("reference", None),
        ("date_start", True),
        ("date_start", False),
        ("date_start", "test"),
        ("date_start", None),
        ("date_start", 4),
        ("date_start", 4.5),
        ("date_start", -1),
        ("date_end", True),
        ("date_end", False),
        ("date_end", "test"),
        ("date_end", None),
        ("date_end", 4),
        ("date_end", 4.5),
        ("date_end", -1),
        ("category_id", "test"),
        ("category_id", 3.5),
        ("category_id", -1),
        ("frequency_id", "test"),
        ("frequency_id", 3.5),
        ("frequency_id", -1),
    ],
)
async def test_create_scheduled_transaction_with_invalid_data(
    test_wallet: models.Wallet,
    test_user: models.User,
    key: str,
    value: Any,
):
    """
    Test creation of scheduled transactions with invalid data.

    Args:
        test_user (fixture): The user it should be tested with.
        test_wallet (fixture): The test wallet for the transactions.
        key: The key that should be updated in the payload.
        value: The value that should be placed on the key.
    """

    payload = {
        "wallet_id": test_wallet.id,
        "amount": 999,
        "reference": "unautherized",
        "date_start": now().isoformat(),
        "date_end": get_tomorrow().isoformat(),
        "category_id": 1,
        "frequency_id": 2,
    }

    payload[key] = value

    res = await make_http_request(
        ENDPOINT,
        json=payload,
        as_user=test_user,
    )

    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "key, value",
    [
        ("wallet_id", "test"),
        ("wallet_id", 3.5),
        ("wallet_id", -1),
        ("amount", "test"),
        ("amount", True),
        ("amount", False),
        ("amount", None),
        ("reference", True),
        ("reference", False),
        ("reference", None),
        ("date_start", True),
        ("date_start", False),
        ("date_start", "test"),
        ("date_start", None),
        ("date_start", 4),
        ("date_start", 4.5),
        ("date_start", -1),
        ("date_end", True),
        ("date_end", False),
        ("date_end", "test"),
        ("date_end", None),
        ("date_end", 4),
        ("date_end", 4.5),
        ("date_end", -1),
        ("category_id", "test"),
        ("category_id", 3.5),
        ("category_id", -1),
        ("frequency_id", "test"),
        ("frequency_id", 3.5),
        ("frequency_id", -1),
    ],
)
async def test_update_scheduled_transaction_with_invalid_data(
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
    test_user: models.User,
    key: str,
    value: Any,
):
    """
    Test updating of scheduled transactions with invalid data.

    Args:
        test_user (fixture): The user it should be tested with.
        test_wallet (fixture): The test wallet for the transactions.
        key: The key that should be updated in the payload.
        value: The value that should be placed on the key.
    """

    transaction = test_wallet_scheduled_transaction_list[0]
    payload = {
        "wallet_id": transaction.wallet_id,
        "amount": 999,
        "reference": "unautherized",
        "date_start": now().isoformat(),
        "date_end": get_tomorrow().isoformat(),
        "category_id": 1,
        "frequency_id": 2,
    }

    payload[key] = value

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        json=payload,
        as_user=test_user,
    )

    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.usefixtures("test_wallet_scheduled_transaction_list")
async def test_update_scheduled_transaction_non_existent(
    test_user: models.User, test_wallet: models.Wallet
):
    """
    Test updating of scheduled transactions that does not exist.

    Args:
        test_user (fixture): The user it should be tested with.
        test_wallet (fixture): The test wallet for the transactions.
    """

    payload = {
        "wallet_id": test_wallet.id,
        "amount": 999,
        "reference": "unautherized",
        "date_start": now().isoformat(),
        "date_end": get_tomorrow().isoformat(),
        "category_id": 1,
        "frequency_id": 2,
    }

    res = await make_http_request(
        ENDPOINT + str(99999), as_user=test_user, json=payload
    )

    assert res.status_code == HTTP_404_NOT_FOUND


async def test_delete_scheduled_transactions_keep_transactions():
    """
    Test the deletion of scheduled transactions while keeping associated transactions.
    """

    # TODO: needs to be implemented


async def test_rate_limiting_scheduled_transactions():
    """
    Test the rate limiting functionality for scheduled transactions in the API.
    """

    # TODO: needs to be implemented


async def test_pagination_scheduled_transactions():
    """
    Test the pagination of scheduled transactions in the API.
    """

    # TODO: needs to be implemented
