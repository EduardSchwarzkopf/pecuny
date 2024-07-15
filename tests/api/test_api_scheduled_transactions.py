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
from app.date_manager import get_tomorrow, get_yesterday
from app.repository import Repository
from app.utils.classes import RoundedDecimal
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import make_http_request

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


async def test_read_scheduled_transaction():
    assert False


async def test_update_scheduled_transaction():
    assert False


async def test_delete_scheduled_transaction():
    assert False


# Tests for unauthorized access
async def test_create_scheduled_transaction_unauthorized():
    assert False


async def test_read_scheduled_transaction_unauthorized():
    assert False


async def test_update_scheduled_transaction_unauthorized():
    assert False


async def test_delete_scheduled_transaction_unauthorized():
    assert False


# Tests for unauthenticated access
async def test_create_scheduled_transaction_unauthenticated():
    assert False


async def test_read_scheduled_transaction_unauthenticated():
    assert False


async def test_update_scheduled_transaction_unauthenticated():
    assert False


async def test_delete_scheduled_transaction_unauthenticated():
    assert False


# Tests for handling non-existent entities
async def test_read_scheduled_transaction_not_found():
    assert False


# Additional tests for enhanced functionality
async def test_create_scheduled_transaction_minimal_data():
    assert False


async def test_create_scheduled_transaction_all_fields():
    assert False


async def test_create_scheduled_transaction_with_missing_fields():
    assert False


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
    assert False


async def test_rate_limiting_scheduled_transactions():
    # TODO: needs to be implemented
    assert False


async def test_pagination_scheduled_transactions():
    # TODO: needs to be implemented
    assert False
