from csv import DictReader
from decimal import InvalidOperation

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


async def import_transactions_from_csv(
    user: models.User,
    account_id: int,
    reader: DictReader,
) -> None:
    """
    Imports a list of transactions for a user.

    Args:
        user: The user for whom the transactions are being imported.
        transaction_data_list: A list of transaction data to be imported.

    Returns:
        None
    """

    async with await db.get_session() as session:

        repo = Repository(session)
        service = TransactionService(repo)
        failed_transaction_list: list[FailedImportedTransaction] = []

        for row in reader:
            failed_transaction = FailedImportedTransaction(**row)
            row_section = row.get("section")
            section_list = await repo.filter_by(
                models.TransactionSection,
                models.TransactionSection.label,
                row_section,
                DatabaseFilterOperator.LIKE,
            )

            if not section_list:
                failed_transaction.reason = f"Section {row_section} not found"
                failed_transaction_list.append(failed_transaction)
                continue

            section = section_list[0]

            conditions = [
                (
                    models.TransactionCategory.label,
                    row.get("category"),
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
            category = category_list[0] if category_list else None

            if category is None:
                failed_transaction.reason = f"Category {row['category']} not found"
                failed_transaction_list.append(failed_transaction)
                continue

            try:

                transaction_data = schemas.TransactionInformationCreate(
                    account_id=account_id, category_id=category.id, **row
                )
            except ValidationError as e:
                first_error = e.errors()[0]
                custom_error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
                failed_transaction.reason = custom_error_message
                failed_transaction_list.append(failed_transaction)
                continue
            except InvalidOperation as e:
                msg = (
                    f"Invalid value on line {reader.line_num} on value {row['amount']}"
                )
                failed_transaction.reason = msg
                failed_transaction_list.append(failed_transaction)
                continue

            transaction = await transaction_manager.transaction(
                service.create_transaction,
                user,
                transaction_data,
                session=session,
            )

            if transaction is None:
                failed_transaction.reason = "Failed to create transaction"
                failed_transaction_list.append(failed_transaction)

    if not settings.is_testing_environment:
        await send_transaction_import_report(
            user, reader.line_num - 1, failed_transaction_list
        )
