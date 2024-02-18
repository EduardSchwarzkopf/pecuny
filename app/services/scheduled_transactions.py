from app import models, schemas, repository as repo
from datetime import datetime
from app.logger import get_logger

logger = get_logger(__name__)


async def get_transaction_list(
    user: models.User, account_id: int, date_start: datetime, date_end: datetime
):
    account = await repo.get(models.Account, account_id)
    if account.user_id == user.id:
        return await repo.get_scheduled_transactions_from_period(
            account_id, date_start, date_end
        )


async def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
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
    account = await repo.get(models.Account, transaction_information.account_id)

    if user.id.bytes != account.user_id.bytes:
        return None

    offset_account_id = transaction_information.offset_account_id

    if offset_account_id:
        offset_account = await repo.get(models.Account, offset_account_id)

        if offset_account is None:
            return None

        if user.id.bytes != offset_account.user_id.bytes:
            raise Exception(
                f"User[id: {user.id}] not allowed to access offset_account[id: {transaction_information.offset_account_id}]"
            )

    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(transaction_information.dict())

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
    logger.info(
        "Deleting scheduled_transaction with ID %s for user %s",
        transaction_id,
        current_user.id,
    )

    transaction = await repo.get(
        models.TransactionScheduled,
        transaction_id,
        load_relationships=["offset_transaction"],
    )

    if transaction is None:
        logger.warning("Scheduled Transaction with ID %s not found.", transaction_id)
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        logger.warning("User ID does not match the account's User ID.")
        return

    await repo.delete(transaction)

    return True
