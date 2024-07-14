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
from app.repository import Repository
from app.utils.classes import RoundedDecimal
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_iso_timestring, get_user_offset_account, make_http_request

ENDPOINT = "/api/scheduled-transactions/"


# Tests for basic CRUD operations
async def test_create_scheduled_transaction():
    assert False


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
