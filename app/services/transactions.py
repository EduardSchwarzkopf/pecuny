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

    # TODO: Check if user is also auth for offset account
    if user.id == account.user_id:

        transaction_information.amount = _handle_transaction_amount(
            transaction_information.amount, transaction_information.subcategory_id
        )

        delattr(transaction_information, "account_id")
        db_transaction_information = models.TransactionInformation()

        utils.update_model_object(db_transaction_information, transaction_information)

        account.balance += transaction_information.amount
        transaction = models.Transaction(
            information=db_transaction_information, account_id=account.id
        )

        repo.save([account, transaction, db_transaction_information]),
        return transaction

    return None


def update_transaction(
    current_user: models.User,
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
):
    transaction = repo.get("Transaction", transaction_id)
    if transaction == None:
        return

    account = repo.get("Account", transaction.account_id)
    if current_user.id == account.user_id:

        amount_updated = transaction_information.amount - transaction.information.amount
        account.balance += amount_updated

        delattr(transaction_information, "account_id")
        utils.update_model_object(transaction.information, transaction_information)

        if transaction.offset_transaction:
            offset_transaction = transaction.offset_transaction
            offset_account = repo.get("Account", offset_transaction.account_id)
            offset_account.balance -= amount_updated

            offset_info = transaction_information
            offset_info.amount = offset_info.amount * -1

            utils.update_model_object(
                transaction.offset_transaction.information, offset_info
            )

        return transaction


def delete_transaction(current_user: models.User, transaction_id: int) -> bool:

    transaction = repo.get("Transaction", transaction_id)

    if transaction == None:
        # No transaction found
        return

    account = repo.get("Account", transaction.account_id)

    if current_user.id != account.user_id:
        # user is not owner of the account
        return

    # handle transaction deletion
    amount = transaction.information.amount
    account.balance -= amount

    if transaction.offset_transaction:
        offset_transaction = transaction.offset_transaction
        offset_account = repo.get("Account", offset_transaction.account_id)
        offset_account.balance += amount
        repo.delete(transaction.offset_transaction)

    repo.delete(transaction)

    return True


def _handle_transaction_amount(amount, subcategory_id):

    subcategory = repo.get("TransactionSubcategory", subcategory_id)
    parent_id = subcategory.parent_category_id

    if parent_id != 1 and amount > 0:
        amount = amount * -1

    return amount
