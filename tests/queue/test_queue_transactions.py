import time
from typing import List

import pytest

from app import models
from app.date_manager import get_today
from app.repository import Repository
from app.tasks import create_transactions_for_batch
from app.utils.enums import DatabaseFilterOperator, Frequency


def _process_scheduled_transactions() -> None:
    create_transactions_for_batch.delay()
    time.sleep(0.3)  # give it some time to process


async def test_create_transactions_from_schedule(
    test_account: models.Account,
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):
    balance = test_account.balance
    account_id = test_account.id

    total_balance = sum(
        transaction.information.amount
        for transaction in test_account_scheduled_transaction_list
    )

    _process_scheduled_transactions()
    repository.session.expire(test_account)

    account = await repository.get(models.Account, account_id)
    new_balance = account.balance

    assert new_balance == balance + total_balance


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_daily_transaction(
    test_account: models.Account,
    repository: Repository,
):
    _process_scheduled_transactions()

    model = models.TransactionScheduled
    daily_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.EQUAL),
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
            (model.frequency_id, Frequency.DAILY.value, DatabaseFilterOperator.EQUAL),
        ],
    )

    assert len(daily_transaction_list) == 1

    daily_transaction = daily_transaction_list[0]

    transaction = await repository.filter_by(
        models.Transaction,
        models.Transaction.scheduled_transaction_id,
        daily_transaction.id,
    )

    assert len(transaction) == 1
    assert transaction[0] is not None


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_weekly_transaction(
    test_account: models.Account,
    repository: Repository,
):
    _process_scheduled_transactions()

    model = models.TransactionScheduled
    weekly_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.EQUAL),
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
            (model.frequency_id, Frequency.WEEKLY.value, DatabaseFilterOperator.EQUAL),
        ],
    )

    assert len(weekly_transaction_list) == 1

    weekly_transaction = weekly_transaction_list[0]

    transaction = await repository.filter_by(
        models.Transaction,
        models.Transaction.scheduled_transaction_id,
        weekly_transaction.id,
    )

    assert len(transaction) == 1
    assert transaction[0] is not None


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_yearly_transaction(
    test_account: models.Account,
    repository: Repository,
):
    _process_scheduled_transactions()

    model = models.TransactionScheduled
    yearly_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.EQUAL),
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
            (model.frequency_id, Frequency.YEARLY.value, DatabaseFilterOperator.EQUAL),
        ],
    )

    assert len(yearly_transaction_list) == 1

    yearly_transaction = yearly_transaction_list[0]

    transaction = await repository.filter_by(
        models.Transaction,
        models.Transaction.scheduled_transaction_id,
        yearly_transaction.id,
    )

    assert len(transaction) == 1
    assert transaction[0] is not None


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_ended(
    test_account: models.Account, repository: Repository
):
    _process_scheduled_transactions()

    model = models.TransactionScheduled

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_end, get_today(), DatabaseFilterOperator.LESS_THAN),
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
        ],
    )

    assert len(scheduled_transaction_list) > 0

    for scheduled_transaction in scheduled_transaction_list:

        created_transaction = await repository.filter_by(
            models.Transaction,
            models.Transaction.scheduled_transaction_id,
            scheduled_transaction.id,
        )

        assert len(created_transaction) == 0


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_not_started(
    test_account: models.Account, repository: Repository
):
    _process_scheduled_transactions()

    model = models.TransactionScheduled

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.LESS_THAN),
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
        ],
    )

    assert len(scheduled_transaction_list) > 0

    for scheduled_transaction in scheduled_transaction_list:

        created_transaction = await repository.filter_by(
            models.Transaction,
            models.Transaction.scheduled_transaction_id,
            scheduled_transaction.id,
        )

        assert len(created_transaction) == 0
