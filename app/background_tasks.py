from csv import DictReader
from decimal import InvalidOperation
from typing import List, Optional

from pydantic import ValidationError

from app import models, schemas, transaction_manager
from app.config import settings
from app.database import db
from app.logger import get_logger
from app.repository import Repository
from app.services.email import send_transaction_import_report
from app.services.transactions import TransactionService
from app.utils.dataclasses_utils import FailedImportedTransaction
from app.utils.enums import DatabaseFilterOperator

logger = get_logger(__name__)


async def _process_transaction_row(
    row: dict,
    line_num: int,
    account_id: int,
    user: models.User,
    repo: Repository,
    service: TransactionService,
) -> Optional[FailedImportedTransaction]:
    """
    Processes a single row from the CSV file and creates a transaction based on its contents.

    Args:
        row: A dictionary representing a row from the CSV file.
        account_id: The account ID to associate with the transaction.
        session: The database session.
        user: The user object.
        repo: The repository for database operations.

    Returns:
        A FailedImportedTransaction instance if the transaction fails, otherwise None.
    """
    row_amount = row.get("amount")
    row_offset_account_id = row.get("offset_account_id")

    amount = float(row_amount) if row_amount else None
    offset_account_id = int(row_offset_account_id) if row_offset_account_id else None

    failed_transaction = FailedImportedTransaction(
        date=row.get("date"),
        amount=amount,
        reference=row.get("reference"),
        category=row.get("category"),
        offset_account_id=offset_account_id,
        section=row.get("section"),
    )

    section_list = await repo.filter_by(
        models.TransactionSection,
        models.TransactionSection.label,
        failed_transaction.section,
        DatabaseFilterOperator.LIKE,
    )

    if not section_list:
        failed_transaction.reason = f"Section {failed_transaction.section} not found"
        return failed_transaction

    section = section_list[0]

    conditions = [
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
    ]

    category_list = await repo.filter_by_multiple(
        models.TransactionCategory, conditions
    )

    if not category_list:
        failed_transaction.reason = f"Category {row['category']} not found"
        return failed_transaction

    category = category_list[0]

    try:
        transaction_data = schemas.TransactionInformationCreate(
            account_id=account_id, category_id=category.id, **row
        )
    except ValidationError as e:
        first_error = e.errors()[0]
        failed_transaction.reason = f"{first_error['loc'][0]}: {first_error['msg']}"
        return failed_transaction
    except InvalidOperation:
        failed_transaction.reason = (
            f"Invalid value on line {line_num} on value {failed_transaction.amount}"
        )
        return failed_transaction

    transaction = await transaction_manager.transaction(
        service.create_transaction,
        user,
        transaction_data,
        session=repo.session,
    )

    if transaction is None:
        failed_transaction.reason = "Failed to create transaction"
        return failed_transaction

    return None


async def import_transactions_from_csv(
    user: models.User, account_id: int, reader: DictReader
) -> None:
    """
    Imports transactions for a user from a CSV file.

    Args:
        user: The user for whom the transactions are being imported.
        account_id: The ID of the account where transactions will be recorded.
        reader: A DictReader object containing transaction rows from a CSV file.

    Returns:
        None. Transactions are imported to the database, and any failures are handled appropriately.
    """
    async with await db.get_session() as session:
        repo = Repository(session)
        service = TransactionService(repo)
        failed_transaction_list: List[FailedImportedTransaction] = []

        for row in reader:
            failed_transaction = await _process_transaction_row(
                row, reader.line_num, account_id, user, repo, service
            )
            if failed_transaction:
                failed_transaction_list.append(failed_transaction)

    if not settings.is_testing_environment:
        await send_transaction_import_report(
            user, reader.line_num - 1, failed_transaction_list
        )
