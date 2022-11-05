from copy import deepcopy
from .. import models, schemas, repository as repo


async def get_transaction_list(
    user: models.User, transaction_query: schemas.TransactionQuery
):

    account_id = transaction_query.account_id
    account = await repo.get(models.Account, account_id)
    if account.user_id == user.id:

        transactions = await repo.get_transactions_from_period(
            account_id, transaction_query.date_start, transaction_query.date_end
        )
        return transactions


async def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
    transaction = await repo.get(models.Transaction, transaction_id)

    if transaction == None:
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

    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(transaction_information.dict())

    account.balance += transaction_information.amount
    transaction = models.Transaction(
        information=db_transaction_information, account_id=account.id
    )

    if transaction_information.offset_account_id:
        offset_transaction = _handle_offset_transaction(user, transaction_information)

        if offset_transaction == None:
            raise Exception(
                f"User[id: {user.id}] not allowed to access offset_account[id: {transaction_information.offset_account_id}]"
            )

        transaction.offset_transaction = offset_transaction
        offset_transaction.offset_transaction = transaction

    await repo.save([account, transaction, db_transaction_information])

    return transaction


async def _handle_offset_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:
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
    if transaction == None:
        return

    account = await repo.get(models.Account, transaction.account_id)
    if current_user.id != account.user_id:
        return

    amount_updated = transaction_information.amount - transaction.information.amount
    account.balance += amount_updated

    if transaction.offset_transaction:
        offset_transaction = transaction.offset_transaction
        offset_account = await repo.get(models.Account, offset_transaction.account_id)

        if offset_account.user_id != current_user.id:
            return

        offset_account.balance -= amount_updated

        offset_info = deepcopy(transaction_information)
        offset_info.amount = offset_info.amount * -1

    return transaction


async def delete_transaction(current_user: models.User, transaction_id: int) -> bool:

    transaction = await repo.get(models.Transaction, transaction_id)

    if transaction == None:
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
