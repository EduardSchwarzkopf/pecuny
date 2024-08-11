import datetime
import time
from typing import List

import pytest

from app import models
from app.date_manager import get_today, get_yesterday
from app.repository import Repository
from app.schemas import TransactionData
from app.services.transactions import TransactionService
from app.tasks import process_scheduled_transactions
from app.utils.enums import DatabaseFilterOperator, Frequency


def _process_scheduled_transactions() -> None:
    """
    Process scheduled transactions asynchronously and
    wait for a short duration for processing to complete.
    """

    process_scheduled_transactions.delay()
    time.sleep(1)  # give it some time to process


async def _assert_transaction_creation(
    frequency: Frequency,
    test_account: models.Account,
    repository: Repository,
):
    """
    Asserts the creation of transactions based on the specified frequency for a test account.

    Args:
        frequency: The frequency of the transactions to be created.
        test_account: The test account for the transactions.
        repository: The repository for database operations.
    """

    model = models.TransactionScheduled
    today = get_today()

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.account_id, test_account.id, DatabaseFilterOperator.EQUAL),
            (model.frequency_id, frequency.value, DatabaseFilterOperator.EQUAL),
            (model.date_start, today, DatabaseFilterOperator.LESS_THAN_OR_EQUAL),
            (model.date_end, today, DatabaseFilterOperator.GREATER_THAN_OR_EQUAL),
        ],
    )

    assert len(scheduled_transaction_list) > 0

    for scheduled_transaction in scheduled_transaction_list:
        transaction_list = await repository.filter_by(
            models.Transaction,
            models.Transaction.scheduled_transaction_id,
            scheduled_transaction.id,
        )

        assert len(transaction_list) > 0
        for transaction in transaction_list:
            assert transaction.account_id == scheduled_transaction.account_id
            assert (
                transaction.information.amount
                == scheduled_transaction.information.amount
            )
            assert (
                transaction.information.reference
                == scheduled_transaction.information.reference
            )


async def test_create_transactions_from_schedule(
    test_account: models.Account,
    test_account_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):
    """
    Test the creation of transactions from a list of scheduled transactions for a test account.

    Args:
        test_account: The test account for the transactions.
        test_account_scheduled_transaction_list:
            List of scheduled transactions for the test account.
        repository: The repository for database operations.
    """

    balance = test_account.balance
    account_id = test_account.id

    total_balance = sum(
        transaction.information.amount
        for transaction in test_account_scheduled_transaction_list
    )

    expected_account_balance = balance + total_balance

    _process_scheduled_transactions()
    repository.session.expire(test_account)

    account = await repository.get(models.Account, account_id)

    assert isinstance(account, models.Account)

    new_balance = account.balance

    assert new_balance == expected_account_balance


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_daily_transaction(
    test_account: models.Account, repository: Repository
):
    """
    Test the creation of daily transactions for a test account.

    Args:
        test_account: The test account for the transaction.
        repository: The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.DAILY, test_account, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_weekly_transaction(
    test_account: models.Account, repository: Repository
):
    """
    Test the creation of weekly transactions for a test account.

    Args:
        test_account: The test account for the transaction.
        repository: The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.WEEKLY, test_account, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_yearly_transaction(
    test_account: models.Account, repository: Repository
):
    """
    Test the creation of yearly transactions for a test account.

    Args:
        test_account: The test account for the transaction.
        repository: The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.YEARLY, test_account, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_ended(
    test_account: models.Account, repository: Repository
):
    """
    Test that scheduled transactions that have ended do not have corresponding created transactions.

    Args:
        test_account: The test account for the transaction.
        repository: The repository for database operations.
    """

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
    """
    Test that scheduled transactions not yet started do not have corresponding created transactions.

    Args:
        test_account: The test account for the transaction.
        repository: The repository for database operations.
    """

    _process_scheduled_transactions()

    model = models.TransactionScheduled

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.GREATER_THAN),
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


async def _assert_scheduled_transaction_already_exist(
    frequency: Frequency,
    test_account: models.Account,
    test_user: models.User,
    repository: Repository,
    date: datetime.datetime = get_yesterday(),
):
    """
    Asserts that a scheduled transaction already exists for the specified frequency and test account.

    Args:
        frequency: The frequency of the scheduled transaction.
        test_account: The test account for the scheduled transaction.
        repository: The repository for database operations.
    """

    scheduled_transaction_list = await repository.filter_by_multiple(
        models.TransactionScheduled,
        [
            (
                models.TransactionScheduled.account_id,
                test_account.id,
                DatabaseFilterOperator.EQUAL,
            ),
            (
                models.TransactionScheduled.frequency_id,
                frequency.value,
                DatabaseFilterOperator.EQUAL,
            ),
        ],
    )

    assert len(scheduled_transaction_list) > 0

    scheduled_transaction = None
    for transaction in scheduled_transaction_list:
        if (
            transaction.information.reference
            == f"scheduled_transaction_{frequency.name}".lower()
        ):
            scheduled_transaction = transaction
            break

    assert scheduled_transaction is not None

    service = TransactionService(repository)

    information = scheduled_transaction.information

    reference = "transaction already exists"

    transaction = await service.create_transaction(
        test_user,
        TransactionData(
            account_id=scheduled_transaction.account.id,
            amount=information.amount,
            reference=reference,
            date=date,
            category_id=information.category_id,
            scheduled_transaction_id=scheduled_transaction.id,
        ),
    )

    await repository.session.commit()

    _process_scheduled_transactions()

    transaction_list = await repository.filter_by_multiple(
        models.Transaction,
        [
            (
                models.Transaction.account_id,
                test_account.id,
                DatabaseFilterOperator.EQUAL,
            ),
            (
                models.Transaction.scheduled_transaction_id,
                scheduled_transaction.id,
                DatabaseFilterOperator.EQUAL,
            ),
        ],
    )

    assert len(transaction_list) == 1

    transaction = transaction_list[0]

    assert transaction.information.reference == reference
    assert transaction.scheduled_transaction_id == scheduled_transaction.id


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_daily_already_exist(
    test_account: models.Account,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a daily scheduled transaction already exists.

    Args:
        test_account: The test account for the transaction.
        test_user: The test user for the transaction.
        repository: The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.DAILY, test_account, test_user, repository, get_today()
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_weekly_already_exist(
    test_account: models.Account,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a weekly scheduled transaction already exists.

    Args:
        test_account: The test account for the transaction.
        test_user: The test user for the transaction.
        repository: The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.WEEKLY, test_account, test_user, repository
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_monthly_already_exist(
    test_account: models.Account,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a monthly scheduled transaction already exists.

    Args:
        test_account: The test account for the transaction.
        test_user: The test user for the transaction.
        repository: The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.MONTHLY, test_account, test_user, repository
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_yearly_already_exist(
    test_account: models.Account,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a yearly scheduled transaction already exists.

    Args:
        test_account: The test account for the transaction.
        test_user: The test user for the transaction.
        repository: The repository for database operations.
    """

    date = get_today() - datetime.timedelta(days=180)
    await _assert_scheduled_transaction_already_exist(
        Frequency.YEARLY, test_account, test_user, repository, date
    )
