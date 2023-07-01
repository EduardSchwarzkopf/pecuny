from datetime import datetime
from app import models, schemas, repository as repo
from pytz import timezone


def localize_datetime(date: datetime) -> datetime:
    return timezone("UTC").localize(date)


async def get_transaction_list(
    user: models.User, account_id: int, date_start: datetime, date_end: datetime
):
    account = await repo.get(models.Account, account_id)
    if account.user_id == user.id:
        return await repo.get_transactions_from_period(account_id, date_start, date_end)


async def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
    transaction = await repo.get(models.Transaction, transaction_id)

    if transaction is None:
        return

    account = await repo.get(models.Account, transaction.account_id)

    if account.user_id == user.id:
        return transaction


async def create_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:
    account = await repo.get(models.Account, transaction_information.account_id)

    if user.id.bytes != account.user_id.bytes:
        return None

    transaction_information.date = localize_datetime(transaction_information.date)
    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(transaction_information.dict())

    account.balance += transaction_information.amount
    transaction = models.Transaction(
        information=db_transaction_information, account_id=account.id
    )

    if transaction_information.offset_account_id:
        offset_transaction = await _handle_offset_transaction(
            user, transaction_information
        )

        if offset_transaction is None:
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
    transaction_information.date = localize_datetime(transaction_information.date)

    offset_account_id = transaction_information.offset_account_id
    offset_account = await repo.get(models.Account, offset_account_id)

    if user.id != offset_account.user_id:
        return None

    transaction_information.amount = transaction_information.amount * -1
    offset_account.balance += transaction_information.amount

    db_offset_transaction_information = models.TransactionInformation()
    db_offset_transaction_information.add_attributes_from_dict(
        transaction_information.dict()
    )
    offset_transcation = models.Transaction(
        information=db_offset_transaction_information,
        account_id=offset_account_id,
    )

    await repo.save(offset_transcation)

    return offset_transcation


async def update_transaction(
    current_user: models.User,
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
):
    transaction = await repo.get(models.Transaction, transaction_id)
    if transaction is None:
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        return

    transaction_information.date = localize_datetime(transaction_information.date)

    amount_updated = (
        round(transaction_information.amount, 2) - transaction.information.amount
    )
    await repo.update(
        models.Account, account.id, **{"balance": account.balance + amount_updated}
    )

    if transaction.offset_transactions_id:
        offset_transaction = await repo.get(
            models.Transaction, transaction.offset_transactions_id
        )
        offset_account = await repo.get(models.Account, offset_transaction.account_id)

        if offset_account.user_id != current_user.id:
            return

        offset_account.balance -= amount_updated
        offset_transaction.information.amount = transaction_information.amount * -1

    await repo.update(
        models.TransactionInformation,
        transaction.information.id,
        **{
            "amount": transaction_information.amount,
            "reference": transaction_information.reference,
            "date": transaction_information.date,
            "category_id": transaction_information.category_id,
        },
    )
    return transaction


async def delete_transaction(current_user: models.User, transaction_id: int) -> bool:
    transaction = await repo.get(
        models.Transaction, transaction_id, load_relationships=["offset_transaction"]
    )

    if transaction is None:
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        return

    amount = transaction.information.amount
    account.balance -= amount

    if transaction.offset_transaction:
        offset_transaction = transaction.offset_transaction
        offset_account = await repo.get(models.Account, offset_transaction.account_id)
        offset_account.balance += amount
        await repo.delete(transaction.offset_transaction)

    await repo.delete(transaction)

    return True
