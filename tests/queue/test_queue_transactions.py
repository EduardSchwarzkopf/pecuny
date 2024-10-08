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
    test_wallet: models.Wallet,
    repository: Repository,
):
    """
    Asserts the creation of transactions based on the specified frequency for a test wallet.

    Args:
        frequency (fixture): The frequency of the transactions to be created.
        test_wallet (fixture): The test wallet for the transactions.
        repository (fixture): The repository for database operations.
    """

    model = models.TransactionScheduled
    today = get_today()

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.wallet_id, test_wallet.id, DatabaseFilterOperator.EQUAL),
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
            assert transaction.wallet_id == scheduled_transaction.wallet_id
            assert (
                transaction.information.amount
                == scheduled_transaction.information.amount
            )
            assert (
                transaction.information.reference
                == scheduled_transaction.information.reference
            )


async def test_create_transactions_from_schedule(
    test_wallet: models.Wallet,
    test_wallet_scheduled_transaction_list: List[models.TransactionScheduled],
    repository: Repository,
):
    """
    Test the creation of transactions from a list of scheduled transactions for a test wallet.

    Args:
        test_wallet (fixture): The test wallet for the transactions.
        test_wallet_scheduled_transaction_list (fixture):
            List of scheduled transactions for the test wallet.
        repository (fixture): The repository for database operations.
    """

    balance = test_wallet.balance
    wallet_id = test_wallet.id

    total_balance = sum(
        transaction.information.amount
        for transaction in test_wallet_scheduled_transaction_list
    )

    expected_wallet_balance = balance + total_balance

    _process_scheduled_transactions()

    wallet = await repository.get(models.Wallet, wallet_id)

    assert wallet is not None

    assert wallet.balance == expected_wallet_balance


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_daily_transaction(
    test_wallet: models.Wallet, repository: Repository
):
    """
    Test the creation of daily transactions for a test wallet.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        repository (fixture): The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.DAILY, test_wallet, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_weekly_transaction(
    test_wallet: models.Wallet, repository: Repository
):
    """
    Test the creation of weekly transactions for a test wallet.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        repository (fixture): The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.WEEKLY, test_wallet, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_create_yearly_transaction(
    test_wallet: models.Wallet, repository: Repository
):
    """
    Test the creation of yearly transactions for a test wallet.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        repository (fixture): The repository for database operations.
    """

    _process_scheduled_transactions()
    await _assert_transaction_creation(Frequency.YEARLY, test_wallet, repository)


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_ended(
    test_wallet: models.Wallet, repository: Repository
):
    """
    Test that scheduled transactions that have ended do not have corresponding created transactions.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        repository (fixture): The repository for database operations.
    """

    _process_scheduled_transactions()

    model = models.TransactionScheduled

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_end, get_today(), DatabaseFilterOperator.LESS_THAN),
            (model.wallet_id, test_wallet.id, DatabaseFilterOperator.EQUAL),
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
    test_wallet: models.Wallet, repository: Repository
):
    """
    Test that scheduled transactions not yet started do not have corresponding created transactions.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        repository (fixture): The repository for database operations.
    """

    _process_scheduled_transactions()

    model = models.TransactionScheduled

    scheduled_transaction_list = await repository.filter_by_multiple(
        model,
        [
            (model.date_start, get_today(), DatabaseFilterOperator.GREATER_THAN),
            (model.wallet_id, test_wallet.id, DatabaseFilterOperator.EQUAL),
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
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
    date: datetime.datetime = get_yesterday(),
):
    """
    Asserts that a scheduled transaction already exists for
    the specified frequency and test wallet.

    Args:
        frequency (fixture): The frequency of the scheduled transaction.
        test_wallet (fixture): The test wallet for the scheduled transaction.
        repository (fixture): The repository for database operations.
    """

    scheduled_transaction_list = await repository.filter_by_multiple(
        models.TransactionScheduled,
        [
            (
                models.TransactionScheduled.wallet_id,
                test_wallet.id,
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

    scheduled_transaction = next(
        (
            transaction_element
            for transaction_element in scheduled_transaction_list
            if (
                transaction_element.information.reference
                == f"scheduled_transaction_{frequency.name}".lower()
            )
        ),
        None,
    )
    assert scheduled_transaction is not None

    service = TransactionService()

    information = scheduled_transaction.information

    reference = "transaction already exists"

    transaction = await service.create_transaction(
        test_user,
        TransactionData(
            wallet_id=scheduled_transaction.wallet.id,
            amount=information.amount,
            reference=reference,
            date=date,
            category_id=information.category_id,
            scheduled_transaction_id=scheduled_transaction.id,
        ),
    )

    _process_scheduled_transactions()

    transaction_list = await repository.filter_by_multiple(
        models.Transaction,
        [
            (
                models.Transaction.wallet_id,
                test_wallet.id,
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
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a daily scheduled transaction already exists.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        test_user (fixture): The test user for the transaction.
        repository (fixture): The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.DAILY, test_wallet, test_user, repository, get_today()
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_weekly_already_exist(
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a weekly scheduled transaction already exists.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        test_user (fixture): The test user for the transaction.
        repository (fixture): The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.WEEKLY, test_wallet, test_user, repository
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_monthly_already_exist(
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a monthly scheduled transaction already exists.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        test_user (fixture): The test user for the transaction.
        repository (fixture): The repository for database operations.
    """

    await _assert_scheduled_transaction_already_exist(
        Frequency.MONTHLY, test_wallet, test_user, repository
    )


@pytest.mark.usefixtures("create_scheduled_transactions")
async def test_scheduled_transaction_yearly_already_exist(
    test_wallet: models.Wallet,
    test_user: models.User,
    repository: Repository,
):
    """
    Test if a yearly scheduled transaction already exists.

    Args:
        test_wallet (fixture): The test wallet for the transaction.
        test_user (fixture): The test user for the transaction.
        repository (fixture): The repository for database operations.
    """

    date = get_today() - datetime.timedelta(days=180)
    await _assert_scheduled_transaction_already_exist(
        Frequency.YEARLY, test_wallet, test_user, repository, date
    )
