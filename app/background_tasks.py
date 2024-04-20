from typing import List

from app import models, schemas, transaction_manager
from app.config import settings
from app.database import db
from app.logger import get_logger
from app.repository import Repository
from app.services.email import send_transaction_import_report
from app.services.transactions import TransactionService

logger = get_logger(__name__)


async def import_transactions(
    user: models.User,
    transaction_data_list: List[schemas.TransactionInformationCreate],
) -> None:
    """
    Imports a list of transactions for a user.

    Args:
        user: The user for whom the transactions are being imported.
        transaction_data_list: A list of transaction data to be imported.

    Returns:
        None
    """

    session = await db.get_session()
    repo = Repository(session)
    transaction_service = TransactionService(repo)
    failed_transaction_list = []

    for transaction_data in transaction_data_list:
        transaction = await transaction_manager.transaction(
            transaction_service.create_transaction,
            user,
            transaction_data,
            session=session,
        )

        if transaction is None:
            failed_transaction_list.append(transaction_data)

    if not settings.is_testing_environment:
        await send_transaction_import_report(
            user, len(transaction_data_list), failed_transaction_list
        )
