from copy import copy, deepcopy
from .. import date_manager, repository as repo, models, schemas, oauth2


# def get(data):

#     account = repo.get("Account", data["account_id"])
#     if auth.is_owner(account):

#         date = date_manager.string_to_datetime(data["date"])

#         transactions = repo.get_from_month(
#             "Transaction", date, "account_id", account.id
#         )

#         return transactions


def create_transaction(
    user: models.User, transaction_information: schemas.TransactionInformationCreate
) -> models.Transaction:

    account = repo.get("Account", transaction_information.account_id)

    # TODO: Check if user is also auth for offset account
    # current_user = oauth2.get_current_user()
    if user.id == account.user_id:

        transaction_information.amount = _handle_transaction_amount(
            transaction_information.amount, transaction_information.subcategory_id
        )

        transaction_information_data = transaction_information.dict()
        del transaction_information_data["account_id"]

        db_transaction_information = models.TransactionInformation(
            **transaction_information_data
        )

        account.balance += transaction_information.amount
        transaction = models.Transaction(
            information=db_transaction_information, account_id=account.id
        )

        repo.save([account, transaction, db_transaction_information]),
        return transaction

    return None


# def update(data):
#     account = repo.get("Account", data["account_id"])

#     if auth.is_owner(account):
#         reference = data["reference"]
#         subcategory_id = data["subcategory"]
#         date = date_manager.string_to_datetime(data["date"])
#         amount = handle_transaction_amount(float(data["amount"]), subcategory_id)

#         transaction = repo.get("Transaction", data["transaction_id"])
#         transaction_information = transaction.information
#         balance_calc = amount - transaction_information.amount
#         account.balance += balance_calc

#         if transaction.offset_transaction:
#             offset_transaction = transaction.offset_transaction
#             offset_account = repo.get("Account", offset_transaction.account_id)
#             offset_account.balance -= balance_calc

#             offset_transaction_information = __update_transaction_information(
#                 offset_transaction.information,
#                 amount * -1,
#                 subcategory_id,
#                 reference,
#                 date,
#             )

#             repo.save([offset_transaction_information, offset_account])

#         transaction_information = __update_transaction_information(
#             transaction_information, amount, subcategory_id, reference, date
#         )

#         repo.save([transaction_information, account])

#         return transaction


# def __update_transaction_information(
#     transaction_information, amount, subcategory_id, reference, date
# ):
#     tf = transaction_information
#     tf.amount = amount
#     tf.subcatgory_id = subcategory_id
#     tf.reference = reference
#     tf.date = date

#     return tf


# def delete(data):

#     transaction = repo.get("Transaction", data["transaction_id"])
#     account = repo.get("Account", transaction.account_id)

#     if auth.is_owner(account):

#         amount = transaction.information.amount
#         account.balance -= amount

#         if transaction.offset_transaction:
#             offset_transaction = transaction.offset_transaction
#             offset_account = repo.get("Account", offset_transaction.account_id)
#             offset_account.balance += amount
#             repo.delete(transaction.offset_transaction)

#         repo.delete(transaction)

#         return True


def _handle_transaction_amount(amount, subcategory_id):

    subcategory = repo.get("TransactionSubcategory", subcategory_id)
    parent_id = subcategory.parent_category_id

    if parent_id != 1 and amount > 0:
        amount = amount * -1

    return amount
