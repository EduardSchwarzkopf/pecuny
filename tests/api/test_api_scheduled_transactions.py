from decimal import Decimal
from typing import List

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
from tests.utils import get_other_user_account, make_http_request

ENDPOINT = "/api/scheduled-transactions/"


# Tests for basic CRUD operations
@pytest.mark.parametrize(
    "amount, reference, category_id, frequency_id",
    [
        (10, "Added 10", 1, 1),
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
    test_account: models.Account,
    test_user: models.User,
):

    yesterday = get_yesterday()
    tomorrow = get_tomorrow()

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": test_account.id,
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
    assert new_transaction.account_id == test_account.id
    assert new_transaction.information.amount == amount
    assert isinstance(json_response["information"]["amount"], float)
    assert isinstance(new_transaction.information.amount, Decimal)
    assert new_transaction.information.reference == reference
    assert new_transaction.date_start == yesterday
    assert new_transaction.date_end == tomorrow


async def test_read_scheduled_transaction(
    test_account: models.Account,
    test_user: models.User,
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), as_user=test_user, method=RequestMethod.GET
    )

    json_response = res.json()
    read_transaction = schemas.ScheduledTransaction(**json_response)

    assert res.status_code == HTTP_200_OK
    assert read_transaction.account_id == test_account.id
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
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

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
            "account_id": transaction.account_id,
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
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):

    transaction = test_account_scheduled_transaction_list[0]
    transaction_id = transaction.id

    res = await make_http_request(
        ENDPOINT + str(transaction_id), as_user=test_user, method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    db_transaction = await repository.get(models.TransactionScheduled, transaction_id)

    assert db_transaction is None


# Tests for unauthorized access
async def test_create_scheduled_transaction_unauthorized(
    test_user: models.User,
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):
    other_account = await get_other_user_account(test_user, repository)

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": other_account.id,
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


@pytest.mark.usefixtures("test_account_scheduled_transaction_list")
async def test_read_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    other_account = await get_other_user_account(test_user, repository)
    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.account_id,
        other_account.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), as_user=test_user, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("test_account_scheduled_transaction_list")
async def test_update_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    other_account = await get_other_user_account(test_user, repository)
    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.account_id,
        other_account.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        json={
            "account_id": other_account.id,
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


@pytest.mark.usefixtures("test_account_scheduled_transaction_list")
async def test_delete_scheduled_transaction_unauthorized(
    test_user: models.User,
    repository: Repository,
):
    other_account = await get_other_user_account(test_user, repository)
    transaction_list = await repository.filter_by(
        models.TransactionScheduled,
        models.TransactionScheduled.account_id,
        other_account.id,
        DatabaseFilterOperator.EQUAL,
    )

    transaction = transaction_list[0]
    transaction_id = transaction.id

    res = await make_http_request(
        ENDPOINT + str(transaction_id), as_user=test_user, method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_404_NOT_FOUND

    transaction_db = await repository.get(models.TransactionScheduled, transaction_id)

    assert isinstance(transaction_db, models.TransactionScheduled)


# Tests for unauthenticated access
async def test_create_scheduled_transaction_unauthenticated(
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": transaction.account_id,
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
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), method=RequestMethod.GET
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


async def test_update_scheduled_transaction_unauthenticated(
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id),
        json={
            "account_id": transaction.account_id,
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
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
):
    transaction = test_account_scheduled_transaction_list[0]

    res = await make_http_request(
        ENDPOINT + str(transaction.id), method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


# Tests for handling non-existent entities
async def test_read_scheduled_transaction_not_found(
    test_user: models.User,
):

    res = await make_http_request(
        ENDPOINT + str(9999), as_user=test_user, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND


# Additional tests for enhanced functionality
@pytest.mark.parametrize(
    "key_to_remove",
    [
        ("account_id"),
        ("amount"),
        ("reference"),
        ("date_start"),
        ("date_end"),
        ("category_id"),
        ("frequency_id"),
    ],
)
async def test_create_scheduled_transaction_with_missing_fields(
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
    test_user: models.User,
    key_to_remove: str,
):
    transaction = test_account_scheduled_transaction_list[0]

    payload = {
        "account_id": transaction.account_id,
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


async def test_create_scheduled_transaction_with_invalid_data():
    assert False


async def test_update_scheduled_transaction_with_invalid_data():
    assert False


async def test_update_scheduled_transaction_non_existent():
    assert False


async def test_partial_update_scheduled_transaction():
    assert False


async def test_delete_scheduled_transactions_keep_transactions():
    # TODO: needs to be implemented
    pass


async def test_rate_limiting_scheduled_transactions():
    # TODO: needs to be implemented
    pass


async def test_pagination_scheduled_transactions():
    # TODO: needs to be implemented
    pass
