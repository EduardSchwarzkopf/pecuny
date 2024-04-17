from typing import List

from sqlalchemy.exc import IntegrityError, PendingRollbackError

from app import models, schemas
from app.config import settings
from app.database import db
from app.logger import get_logger
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

    transaction_service = TransactionService()
    failed_transaction_list = []

    for transaction_data in transaction_data_list:
        try:
            async with db.session as session:
                await transaction_service.create_transaction(user, transaction_data)
                await session.commit()

        except (IntegrityError, PendingRollbackError, Exception) as e:
            logger.warning(e)
            failed_transaction_list.append(transaction_data)

    if settings.is_testing_environment:
        return

    await send_transaction_import_report(
        user, len(transaction_data_list), failed_transaction_list
    )
