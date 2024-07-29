import time
from typing import List

import pytest
from sqlalchemy import and_, exists, func, select

from app import models
from app.date_manager import get_today
from app.repository import Repository
from app.tasks import process_scheduled_transactions
from app.utils.enums import DatabaseFilterOperator, Frequency


def _process_scheduled_transactions() -> None:
    process_scheduled_transactions.delay()
    time.sleep(0.5)  # give it some time to process


async def _assert_transaction_creation(
    frequency: Frequency,
    test_account: models.Account,
    repository: Repository,
):
    model = models.TransactionScheduled
    today = get_today()

    result = await repository.session.execute(
        select(model).where(
            and_(
                model.date_start <= today,
                model.date_end >= today,
                model.is_active == True,
                model.account_id == test_account.id,
                model.frequency_id == frequency.value,
                exists().where(
                    and_(
                        models.Transaction.scheduled_transaction_id == model.id,
                        func.date(models.Transaction.created_at) == func.date(today),
                    )
                ),
            )
        )
    )

    transaction_list = result.unique().scalars().all()

    assert len(transaction_list) > 0

    for transaction in transaction_list:
        assert transaction.date_start <= today
        assert transaction.date_end >= today
        assert transaction.is_active
        assert transaction.account_id == test_account.id
        assert transaction.frequency_id == frequency.value


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

    current_account_balance = balance + total_balance

    _process_scheduled_transactions()
    repository.session.expire(test_account)

    account = await repository.get(models.Account, account_id)
    new_balance = account.balance

    assert new_balance == current_account_balance


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_daily_transaction(
    test_account: models.Account, repository: Repository
):
    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.DAILY, test_account, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_weekly_transaction(
    test_account: models.Account, repository: Repository
):
    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.WEEKLY, test_account, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_yearly_transaction(
    test_account: models.Account, repository: Repository
):
    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.YEARLY, test_account, repository)


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
