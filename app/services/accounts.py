from typing import List
from .. import models, schemas, repository as repo


async def get_accounts(current_user: models.User) -> List[models.Account]:
    account_list = await repo.filter_by(models.Account, "user_id", current_user.id)

    return account_list


async def get_account(current_user: models.User, account_id: int) -> models.Account:

    account = await repo.get(models.Account, account_id)
    if account and account.user_id == current_user.id:
        return account

    return None


async def create_account(user: models.User, account: schemas.Account) -> models.Account:

    db_account = models.Account(user=user, **account.dict())
    await repo.save(db_account)
    return db_account


async def update_account(
    current_user: models.User, account_id, account: schemas.AccountData
) -> models.Account:

    db_account = await repo.get(models.Account, account_id)
    if db_account.user_id == current_user.id:
        await repo.update(models.Account, db_account.id, **account.dict())
        return db_account

    return None


async def delete_account(current_user: models.User, account_id: int) -> bool:

    account = await repo.get(models.Account, account_id)
    if account and account.user_id == current_user.id:
        await repo.delete(account)
        return True

    return None
