import csv
from datetime import datetime
from decimal import InvalidOperation
from io import StringIO
from typing import List, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from app import models, schemas
from app.celery import celery
from app.config import settings
from app.date_manager import get_today
from app.exceptions.base_service_exception import EntityNotFoundException
from app.exceptions.wallet_service_exceptions import WalletAccessDeniedException
from app.repository import Repository
from app.services.email import send_transaction_import_report
from app.services.transactions import TransactionService
from app.utils.dataclasses_utils import FailedImportedTransaction
from app.utils.enums import DatabaseFilterOperator, Frequency


async def _process_transaction_row(
    row: dict,
    line_num: int,
    wallet_id: int,
    user: models.User,
    repo: Repository,
    service: TransactionService,
) -> Optional[FailedImportedTransaction]:
    """
    Processes a single row from the CSV file and creates a transaction based on its contents.

    Args:
        row: A dictionary representing a row from the CSV file.
        wallet_id: The wallet ID to associate with the transaction.
        session: The database session.
        user: The user object.
        repo: The repository for database operations.

    Returns:
        A FailedImportedTransaction instance if the transaction fails, otherwise None.
    """
    row_amount = row.get("amount")
    row_offset_wallet_id = row.get("offset_wallet_id")

    amount = float(row_amount) if row_amount else None
    offset_wallet_id = int(row_offset_wallet_id) if row_offset_wallet_id else None

    failed_transaction = FailedImportedTransaction(
        date=row.get("date"),
        amount=amount,
        reference=row.get("reference"),
        category=row.get("category"),
        offset_wallet_id=offset_wallet_id,
        section=row.get("section"),
    )

    section_list = await repo.filter_by(
        models.TransactionSection,
        models.TransactionSection.label,
        failed_transaction.section,
        DatabaseFilterOperator.LIKE,
    )

    section = section_list[0] if section_list else None

    if section is None:
        failed_transaction.reason = f"Section {failed_transaction.section} not found"
        return failed_transaction

    category_list = await repo.filter_by_multiple(
        models.TransactionCategory,
        [
            (
                models.TransactionCategory.label,
                failed_transaction.category,
                DatabaseFilterOperator.LIKE,
            ),
            (
                models.TransactionCategory.section_id,
                section.id,
                DatabaseFilterOperator.EQUAL,
            ),
        ],
    )

    if not category_list:
        failed_transaction.reason = f"Category {row['category']} not found"
        return failed_transaction

    category = category_list[0]

    try:
        transaction_data = schemas.TransactionData(
            wallet_id=wallet_id,
            category_id=category.id,
            **row,
        )
    except (ValidationError, Exception) as e:
        error_message = ""
        if isinstance(e, ValidationError):
            first_error = e.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
        elif isinstance(e, InvalidOperation):
            error_message = (
                f"Invalid value on line {line_num} on value {failed_transaction.amount}"
            )
        else:
            error_message = str(e)

        failed_transaction.reason = error_message
        return failed_transaction

    try:
        await service.create_transaction(
            user,
            transaction_data,
        )
    except (EntityNotFoundException, WalletAccessDeniedException) as e:
        failed_transaction.reason = e.message
        return failed_transaction

    return None


@celery.task
async def import_transactions_from_csv(
    user_id: int, wallet_id: int, contents: bytes
) -> None:
    """
    Imports transactions for a user from a CSV file.

    Args:
        user: The user for whom the transactions are being imported.
        wallet_id: The ID of the wallet where transactions will be recorded.
        reader: A DictReader object containing transaction rows from a CSV file.

    Returns:
        None. Transactions are imported to the database, and any failures are handled appropriately.
    """
    try:
        contents_str = contents.decode()
        csv_file = StringIO(contents_str)
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=e.reason) from e

    reader = csv.DictReader(csv_file, delimiter=";")

    repo = Repository()
    # TODO: Use user service here:
    user = await repo.get(models.User, user_id)

    service = TransactionService()
    failed_transaction_list: List[FailedImportedTransaction] = []

    for row in reader:
        failed_transaction = await _process_transaction_row(
            row, reader.line_num, wallet_id, user, repo, service
        )
        if failed_transaction:
            failed_transaction_list.append(failed_transaction)

    if settings.environment != "test":
        await send_transaction_import_report(
            user, reader.line_num - 1, failed_transaction_list
        )

    return None


async def _create_transaction(
    today: datetime,
    service: TransactionService,
    repo: Repository,
    scheduled_transaction: models.TransactionScheduled,
):
    """
    Create a transaction based on a scheduled transaction.

        Args:
            session: The database session.
            today: The current date.
            service: The transaction service.
            repo: The repository for database operations.
            scheduled_transaction:
                The scheduled transaction to create a transaction from.
    """

    user = await repo.get(models.User, scheduled_transaction.wallet.user_id)

    information: models.TransactionInformation = scheduled_transaction.information
    new_transaction = schemas.TransactionData(
        wallet_id=scheduled_transaction.wallet.id,
        amount=information.amount,
        reference=information.reference,
        date=today,
        category_id=information.category_id,
        scheduled_transaction_id=scheduled_transaction.id,
    )

    await service.create_transaction(user, new_transaction)


@celery.task
async def process_scheduled_transactions():
    """
    Process scheduled transactions by fetching them based on frequency and
    creating corresponding transactions.
    """

    repo = Repository()
    service = TransactionService()
    today = get_today()

    scheduled_transaction_list = []

    for frequency in Frequency.get_list():
        transactions = await repo.get_scheduled_transactions_by_frequency(
            frequency.value, today
        )
        scheduled_transaction_list += transactions

    if not scheduled_transaction_list:
        return

    for scheduled in scheduled_transaction_list:
        await _create_transaction(
            repo=repo,
            today=today,
            service=service,
            scheduled_transaction=scheduled,
        )
