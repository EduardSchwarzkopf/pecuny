from .. import repository as repo
from models import Account, User


def get_accounts(current_user: User):
    accounts = repo.filter("Account", "user_id", current_user.id)

    return accounts


def get_account(current_user: User, account_id: int) -> Account:

    account = repo.get("Account", account_id)
    if account.user_id == current_user.id:
        return account

    return None


def create_account(current_user: User, account: Account) -> Account:

    account = Account(
        user_id=current_user.id,
        **account.dict(),
    )

    repo.save(account)

    return account


def update(current_user: User, account: Account) -> Account:

    if account._user_id == current_user.id:
        repo.save(account)

        return account


def delete(current_user: User, account_id: int):

    account = repo.get("Account", account_id)

    if account.user_id == current_user.id:

        repo.delete(account)
        return True
