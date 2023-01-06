from app import models, schemas, repository as repo


async def create_scheduled_transaction(
    user: models.User,
    transaction_information: schemas.ScheduledTransactionInformationCreate,
) -> models.Transaction:

    account = await repo.get(models.Account, transaction_information.account_id)

    if user.id.bytes != account.user_id.bytes:
        return None

    db_transaction_information = models.TransactionInformation()
    db_transaction_information.add_attributes_from_dict(transaction_information.dict())

    # TODO: Frequency
    # TODO: date_start, date_end
    # TODO: Offset account
    transaction = models.TransactionScheduled(
        information=db_transaction_information, account_id=account.id
    )

    await repo.save([transaction, db_transaction_information])

    return transaction
