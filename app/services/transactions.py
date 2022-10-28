from copy import deepcopy
from .. import repository as repo, models, schemas, utils


def get_transaction_list(
    user: models.User, transaction_query: schemas.TransactionQuery
):

    account_id = transaction_query.account_id
    account = repo.get("Account", account_id)
    if account.user_id == user.id:

        transactions = repo.get_transactions_from_period(
            account_id, transaction_query.date_start, transaction_query.date_end
        )
        return transactions


def get_transaction(user: models.User, transaction_id: int) -> models.Transaction:
    transaction = repo.get("Transaction", transaction_id)

    if transaction == None:
        return

    account = repo.get("Account", transaction.account_id)

    if account.user_id == user.id:
        return transaction


def create_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:

    account = repo.get("Account", transaction_information.account_id)

    if user.id != account.user_id:
        return None

    db_transaction_information = models.TransactionInformation()

    utils.update_model_object(db_transaction_information, transaction_information)

    account.balance += transaction_information.amount
    transaction = models.Transaction(
        information=db_transaction_information, account_id=account.id
    )

    if transaction_information.offset_account_id:
        offset_transaction = _handle_offset_transaction(user, transaction_information)

        if offset_transaction == None:
            return None

        transaction.offset_transaction = offset_transaction
        offset_transaction.offset_transaction = transaction

    repo.save([account, transaction, db_transaction_information])

    return transaction


def _handle_offset_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:
    offset_account_id = transaction_information.offset_account_id
    offset_account = repo.get("Account", offset_account_id)

    if user.id != offset_account.user_id:
        return None

    transaction_information.amount = transaction_information.amount * -1
    offset_account.balance += transaction_information.amount

    db_offset_transaction_information = models.TransactionInformation()
    utils.update_model_object(
        db_offset_transaction_information, transaction_information
    )

    offset_transcation = models.Transaction(
        information=db_offset_transaction_information,
        account_id=offset_account_id,
    )

    repo.save(offset_transcation)

    return offset_transcation


def update_transaction(
    current_user: models.User,
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
):
    transaction = repo.get("Transaction", transaction_id)
    if transaction == None:
        return

    account = repo.get("Account", transaction.account_id)
    if current_user.id != account.user_id:
        return

    amount_updated = transaction_information.amount - transaction.information.amount
    account.balance += amount_updated

    if transaction.offset_transaction:
        offset_transaction = transaction.offset_transaction
        offset_account = repo.get("Account", offset_transaction.account_id)

        if offset_account.user_id != current_user.id:
            return

        offset_account.balance -= amount_updated

        offset_info = deepcopy(transaction_information)
        offset_info.amount = offset_info.amount * -1

        utils.update_model_object(
            transaction.offset_transaction.information, offset_info
        )

    utils.update_model_object(transaction.information, transaction_information)

    return transaction


def delete_transaction(current_user: models.User, transaction_id: int) -> bool:

    transaction = repo.get("Transaction", transaction_id)

    if transaction == None:
        return

    account = repo.get("Account", transaction.account_id)
    if current_user.id != account.user_id:
        return

    amount = transaction.information.amount
    account.balance -= amount

    if transaction.offset_transaction:
        offset_transaction = transaction.offset_transaction
        offset_account = repo.get("Account", offset_transaction.account_id)
        offset_account.balance += amount
        repo.delete(transaction.offset_transaction)

    repo.delete(transaction)

    return True
