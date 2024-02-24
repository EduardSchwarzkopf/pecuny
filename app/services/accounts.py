from typing import List

from app import models
from app import repository as repo
from app import schemas
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


async def get_accounts(current_user: models.User) -> List[models.Account]:
    """
    Retrieves a list of accounts.

    Args:
        current_user: The current active user.

    Returns:
        List[Account]: A list of account objects.
    """

    logger.info(f"Getting accounts for user: {current_user.id}")
    accounts = await repo.filter_by(models.Account, "user_id", current_user.id)
    logger.info(f"Found {len(accounts)} accounts for user: {current_user.id}")
    return accounts


async def get_account(current_user: models.User, account_id: int) -> models.Account:
    """
    Retrieves an account by ID.

    Args:
        current_user: The current active user.
        account_id: The ID of the account to retrieve.

    Returns:
        Account: The retrieved account object.
    """

    logger.info(f"Getting account {account_id} for user: {current_user.id}")
    account = await repo.get(models.Account, account_id)
    if account and account.user_id == current_user.id:
        logger.info(f"Found account {account_id} for user: {current_user.id}")
        return account
    logger.warning(
        f"Account {account_id} not found or does not belong to user: {current_user.id}"
    )
    return None


async def create_account(user: models.User, account: schemas.Account) -> models.Account:
    """
    Creates a new account.

    Args:
        user: The user object.
        account: The account data.

    Returns:
        Account: The created account object.
    """

    logger.info(f"Creating new account for user: {user.id}")
    db_account = models.Account(user=user, **account.dict())
    await repo.save(db_account)
    logger.info(f"Account {db_account.id} created for user: {user.id}")
    return db_account


async def update_account(
    current_user: models.User, account_id, account: schemas.AccountData
) -> models.Account:
    """
    Updates an account.

    Args:
        current_user: The current active user.
        account_id: The ID of the account to update.
        account: The updated account data.

    Returns:
        Account: The updated account information.
    """

    logger.info(f"Updating account {account_id} for user: {current_user.id}")
    db_account = await repo.get(models.Account, account_id)
    if db_account.user_id == current_user.id:
        await repo.update(models.Account, db_account.id, **account.dict())
        logger.info(f"Account {account_id} updated for user: {current_user.id}")
        return db_account
    logger.warning(
        f"Account {account_id} not found or does not belong to user: {current_user.id}"
    )
    return None


async def delete_account(current_user: models.User, account_id: int) -> bool:
    """
    Deletes an account.

    Args:
        current_user: The current active user.
        account_id: The ID of the account to delete.

    Returns:
        bool: True if the account is successfully deleted, False otherwise.
    """

    logger.info(f"Deleting account {account_id} for user: {current_user.id}")
    account = await repo.get(models.Account, account_id)
    if account and account.user_id == current_user.id:
        await repo.delete(account)
        logger.info(f"Account {account_id} deleted for user: {current_user.id}")
        return True
    logger.warning(
        f"Account {account_id} not found or does not belong to user: {current_user.id}"
    )
    return None


async def check_max_accounts(user: models.User) -> bool:
    """
    Checks if the maximum number of accounts has been reached for a user.

    Args:
        user: The user object.

    Returns:
        bool: True if the maximum number of accounts has been reached, False otherwise.
    """

    logger.info(f"Checking if maximum accounts reached for user: {user.id}")
    account_list = await get_accounts(user)
    result = len(account_list) >= settings.max_allowed_accounts
    if result:
        logger.warning(
            f"User {user.id} has reached the maximum allowed accounts limit."
        )
    return result
