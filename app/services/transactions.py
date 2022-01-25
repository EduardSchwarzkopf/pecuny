from copy import copy, deepcopy
from app import date_manager
from app.accounting.transaction.transaction_util import handle_transaction_amount
from app import (
    repository as repo,
    authorization_manager as auth,
)
from app.models import (
    Transaction,
    TransactionInformation,
)


def get(data):

    account = repo.get("Account", data["account_id"])
    if auth.is_owner(account):

        date = date_manager.string_to_datetime(data["date"])

        transactions = repo.get_from_month(
            "Transaction", date, "account_id", account.id
        )

        return transactions


def create(data):

    account = repo.get("Account", data["account_id"])

    # TODO: Check if user is also auth for offset account
    if auth.is_owner(account):
        transaction = create_intern(data, account)
        return transaction


def create_intern(data, account=None):

    if account == None:
        account = repo.get("Account", data["account_id"])

    account_id = account.id
    reference = data["reference"]
    subcategory = data["subcategory"]
    date = date_manager.string_to_datetime(data["date"])
    amount = handle_transaction_amount(float(data["amount"]), subcategory)

    offset_account = None
    offset_account_id = data["offset_account_id"] or None

    transaction_information = TransactionInformation(
        amount=amount,
        reference=reference,
        subcategory_id=subcategory,
        date=date,
    )

    offset_information = None
    if offset_account_id:
        offset_information = deepcopy(transaction_information)

    account.balance += amount
    transaction = Transaction(
        information=transaction_information, account_id=account_id
    )

    if offset_account_id:
        offset_account = repo.get("Account", offset_account_id)
        offset_account.balance -= amount

        offset_information.amount *= -1

        offset_transaction = Transaction(
            information=offset_information,
            account_id=offset_account.id,
            offset_transaction=transaction,
        )

        transaction.offset_transaction = offset_transaction

        repo.save(offset_information)
        repo.save(offset_transaction)

    repo.save(transaction)
    repo.save(transaction_information)
    repo.save(account)

    return transaction


def update(data):
    account = repo.get("Account", data["account_id"])

    if auth.is_owner(account):
        reference = data["reference"]
        subcategory_id = data["subcategory"]
        date = date_manager.string_to_datetime(data["date"])
        amount = handle_transaction_amount(float(data["amount"]), subcategory_id)

        transaction = repo.get("Transaction", data["transaction_id"])
        transaction_information = transaction.information
        balance_calc = amount - transaction_information.amount
        account.balance += balance_calc

        if transaction.offset_transaction:
            offset_transaction = transaction.offset_transaction
            offset_account = repo.get("Account", offset_transaction.account_id)
            offset_account.balance -= balance_calc

            offset_transaction_information = __update_transaction_information(
                offset_transaction.information,
                amount * -1,
                subcategory_id,
                reference,
                date,
            )

            repo.save([offset_transaction_information, offset_account])

        transaction_information = __update_transaction_information(
            transaction_information, amount, subcategory_id, reference, date
        )

        repo.save([transaction_information, account])

        return transaction


def __update_transaction_information(
    transaction_information, amount, subcategory_id, reference, date
):
    tf = transaction_information
    tf.amount = amount
    tf.subcatgory_id = subcategory_id
    tf.reference = reference
    tf.date = date

    return tf


def delete(data):

    transaction = repo.get("Transaction", data["transaction_id"])
    account = repo.get("Account", transaction.account_id)

    if auth.is_owner(account):

        amount = transaction.information.amount
        account.balance -= amount

        if transaction.offset_transaction:
            offset_transaction = transaction.offset_transaction
            offset_account = repo.get("Account", offset_transaction.account_id)
            offset_account.balance += amount
            repo.delete(transaction.offset_transaction)

        repo.delete(transaction)

        return True
