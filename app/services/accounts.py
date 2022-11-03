from typing import List
from .. import models, schemas


async def get_accounts(current_user: models.User) -> List[models.Account]:
    account_list = await models.Account.filter("user_id", current_user.id)

    return account_list


async def get_account(current_user: models.User, account_id: int) -> models.Account:

    account = await models.Account.get(account_id)
    if account and account.user_id == current_user.id:
        return account

    return None


async def create_account(user: models.User, account: schemas.Account) -> models.Account:

    db_account = await models.Account.create(user=user, **account.dict())
    return db_account


async def update_account(
    current_user: models.User, account_id, account: schemas.AccountData
) -> models.Account:

    db_account = await models.Account.get(account_id)
    if db_account.user_id == current_user.id:
        await db_account.update(account_id, **account.dict())
        return db_account

    return None


async def delete_account(current_user: models.User, account_id: int) -> bool:

    account = await models.Account.get(account_id)
    if account and account.user_id == current_user.id:
        account.delete(account_id)
        return True

    return None
