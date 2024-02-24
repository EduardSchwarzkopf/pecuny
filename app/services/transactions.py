from datetime import datetime

from utils.log_messages import ACCOUNT_USER_ID_MISMATCH

from app import models
from app import repository as repo
from app import schemas
from app.logger import get_logger

logger = get_logger(__name__)


async def get_transaction_list(
    user: models.User, account_id: int, date_start: datetime, date_end: datetime
):
    logger.info(
        "Starting transaction list retrieval for user %s and account %s",
        user.id,
        account_id,
    )
    account = await repo.get(models.Account, account_id)
    if account.user_id == user.id:
        logger.info("User ID verified. Retrieving transactions.")
        return await repo.get_transactions_from_period(account_id, date_start, date_end)
    else:
        logger.warning(ACCOUNT_USER_ID_MISMATCH)


async def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
    logger.info(
        "Retrieving transaction with ID %s for user %s", transaction_id, user.id
    )
    transaction = await repo.get(models.Transaction, transaction_id)

    if transaction is None:
        logger.warning("Transaction with ID %s not found.", transaction_id)
        return

    account = await repo.get(models.Account, transaction.account_id)

    if account.user_id == user.id:
        logger.info("User ID verified. Returning transaction.")
        return transaction
    else:
        logger.warning(ACCOUNT_USER_ID_MISMATCH)


async def create_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:
    logger.info("Creating new transaction for user %s", user.id)
    account = await repo.get(models.Account, transaction_information.account_id)

    if user.id.bytes != account.user_id.bytes:
        logger.warning(ACCOUNT_USER_ID_MISMATCH)
        return None

    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(transaction_information.dict())

    account.balance += transaction_information.amount
    transaction = models.Transaction(
        information=db_transaction_information, account_id=account.id
    )

    if transaction_information.offset_account_id:
        logger.info("Handling offset account for transaction.")
        offset_transaction = await _handle_offset_transaction(
            user, transaction_information
        )

        if offset_transaction is None:
            logger.warning(
                "User[id: %s] not allowed to access offset_account[id: %s]",
                user.id,
                transaction_information.offset_account_id,
            )
            raise Exception(
                f"User[id: {user.id}] not allowed to access offset_account[id: {transaction_information.offset_account_id}]"
            )

        transaction.offset_transaction = offset_transaction
        offset_transaction.offset_transaction = transaction
        await repo.save(offset_transaction)

    await repo.save([account, transaction, db_transaction_information])

    return transaction


async def _handle_offset_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:
    logger.info("Handling offset transaction for user %s", user.id)
    offset_account_id = transaction_information.offset_account_id
    offset_account = await repo.get(models.Account, offset_account_id)

    if user.id != offset_account.user_id:
        logger.warning("User ID does not match the offset account's User ID.")
        return None

    transaction_information.amount = transaction_information.amount * -1
    offset_account.balance += transaction_information.amount

    db_offset_transaction_information = models.TransactionInformation()
    db_offset_transaction_information.add_attributes_from_dict(
        transaction_information.dict()
    )
    offset_transaction = models.Transaction(
        information=db_offset_transaction_information,
        account_id=offset_account_id,
    )

    await repo.save(offset_transaction)

    return offset_transaction


async def update_transaction(
    current_user: models.User,
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
):
    logger.info(
        "Updating transaction with ID %s for user %s", transaction_id, current_user.id
    )
    transaction = await repo.get(models.Transaction, transaction_id)
    if transaction is None:
        logger.warning("Transaction with ID %s not found.", transaction_id)
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        logger.warning(ACCOUNT_USER_ID_MISMATCH)
        return

    amount_updated = (
        round(transaction_information.amount, 2) - transaction.information.amount
    )

    update_info = {"balance": account.balance + amount_updated}
    await repo.update(models.Account, account.id, **update_info)

    if transaction.offset_transactions_id:
        logger.info("Handling offset transaction for update.")
        offset_transaction = await repo.get(
            models.Transaction, transaction.offset_transactions_id
        )
        offset_account = await repo.get(models.Account, offset_transaction.account_id)

        if offset_account.user_id != current_user.id:
            logger.warning("User ID does not match the offset account's User ID.")
            return

        offset_account.balance -= amount_updated
        offset_transaction.information.amount = transaction_information.amount * -1

    update_info = {
        "amount": transaction_information.amount,
        "reference": transaction_information.reference,
        "date": transaction_information.date,
        "category_id": transaction_information.category_id,
    }

    await repo.update(
        models.TransactionInformation,
        transaction.information.id,
        **update_info,
    )

    return transaction


async def delete_transaction(current_user: models.User, transaction_id: int) -> bool:
    logger.info(
        "Deleting transaction with ID %s for user %s", transaction_id, current_user.id
    )
    transaction = await repo.get(
        models.Transaction,
        transaction_id,
        load_relationships=[models.Transaction.offset_transaction],
    )

    if transaction is None:
        logger.warning("Transaction with ID %s not found.", transaction_id)
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        logger.warning(ACCOUNT_USER_ID_MISMATCH)
        return

    amount = transaction.information.amount
    account.balance -= amount

    if transaction.offset_transaction:
        logger.info("Handling offset transaction for delete.")
        offset_transaction = transaction.offset_transaction
        offset_account = await repo.get(models.Account, offset_transaction.account_id)
        offset_account.balance += amount
        await repo.delete(transaction.offset_transaction)

    await repo.delete(transaction)

    return True
