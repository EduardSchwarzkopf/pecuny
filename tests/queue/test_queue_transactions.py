# use fixture for scheduled transactions
import time
from typing import List

from app import models
from app.repository import Repository
from app.tasks import create_transactions_for_batch
from app.utils.enums import DatabaseFilterOperator


async def test_create_daily_transaction(
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

    create_transactions_for_batch.delay()

    time.sleep(1)
    repository.session.expire_all()

    created_transaction_list = await repository.filter_by_multiple(
        models.Transaction,
        [
            (
                models.Transaction.scheduled_transaction_id,
                None,
                DatabaseFilterOperator.IS_NOT,
            ),
            (models.Transaction.account_id, account_id, DatabaseFilterOperator.EQUAL),
        ],
    )
    account = await repository.get(models.Account, account_id)
    new_balance = account.balance

    assert new_balance == balance + total_balance


def test_create_weekly_transaction():
    assert False


def test_create_yearly_transaction():
    assert False


def test_scheduled_transaction_date_end():
    assert False


def test_scheduled_transaction_date_start():
    assert False
