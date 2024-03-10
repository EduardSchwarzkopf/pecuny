from datetime import datetime

from app import models
from app import repository as repo
from app import schemas
from app.logger import get_logger
from app.utils.account_utils import has_user_access_to_account
from app.utils.exceptions import AccessDeniedError

logger = get_logger(__name__)


async def get_transaction_list(
    user: models.User, account_id: int, date_start: datetime, date_end: datetime
):
    """
    Retrieves a list of transactions within a specified period for a given account.

    Args:
        user: The user object.
        account_id: The ID of the account.
        date_start: The start date of the period.
        date_end: The end date of the period.

    Returns:
        list[Transaction]: A list of transactions within the specified period.

    Raises:
        None
    """

    account = await repo.get(models.Account, account_id)
    if account.user_id == user.id:
        return await repo.get_scheduled_transactions_from_period(
            account_id, date_start, date_end
        )


async def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
    """
    Retrieves a transaction by ID.

    Args:
        user: The user object.
        transaction_id: The ID of the transaction to retrieve.

    Returns:
        Transaction: The retrieved transaction.

    Raises:
        None
    """

    transaction = await repo.get(models.TransactionScheduled, transaction_id)

    if transaction is None:
        return

    account = await repo.get(models.Account, transaction.account_id)

    if account.user_id == user.id:
        return transaction


async def create_scheduled_transaction(
    user: models.User,
    transaction_information: schemas.ScheduledTransactionInformationCreate,
) -> models.TransactionScheduled:
    """
    Creates a scheduled transaction.

    Args:
        user: The user object.
        transaction_information: The information for the scheduled transaction.

    Returns:
        TransactionScheduled: The created scheduled transaction.

    Raises:
        None
    """

    account = await repo.get(models.Account, transaction_information.account_id)

    if not has_user_access_to_account(user, account):
        return None

    offset_account_id = transaction_information.offset_account_id

    if offset_account_id:
        offset_account = await repo.get(models.Account, offset_account_id)

        if offset_account is None:
            return None

        if not has_user_access_to_account(user, offset_account):
            raise AccessDeniedError(
                (
                    f"User[id: {user.id}] not allowed to access "
                    f"offset_account[id: {transaction_information.offset_account_id}]"
                )
            )

    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(
        transaction_information.model_dump()
    )

    transaction = models.TransactionScheduled(
        frequency_id=transaction_information.frequency_id,
        date_start=transaction_information.date_start,
        date_end=transaction_information.date_end,
        information=db_transaction_information,
        account_id=account.id,
        offset_account_id=offset_account_id,
    )

    await repo.save([transaction, db_transaction_information])

    return transaction


async def delete_scheduled_transaction(
    current_user: models.User, transaction_id: int
) -> bool:
    """
    Deletes a scheduled transaction.

    Args:
        current_user: The current active user.
        transaction_id: The ID of the scheduled transaction to delete.

    Returns:
        bool: True if the scheduled transaction is successfully deleted, False otherwise.
    """

    logger.info(
        "Deleting scheduled_transaction with ID %s for user %s",
        transaction_id,
        current_user.id,
    )

    transaction = await repo.get(
        models.TransactionScheduled,
        transaction_id,
        load_relationships_list=[models.Transaction.offset_transaction],
    )

    if transaction is None:
        logger.warning("Scheduled Transaction with ID %s not found.", transaction_id)
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        return

    await repo.delete(transaction)

    return True
