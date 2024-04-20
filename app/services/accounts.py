from typing import Optional

from app import models, schemas
from app.config import settings
from app.logger import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class AccountService(BaseService):

    async def get_accounts(
        self, current_user: models.User
    ) -> Optional[list[models.Account]]:
        """
        Retrieves a list of accounts.

        Args:
            current_user: The current active user.

        Returns:
            list[Account]: A list of account objects.
        """

        return await self.repository.filter_by(
            models.Account, models.Account.user_id, current_user.id
        )

    async def get_account(
        self, current_user: models.User, account_id: int
    ) -> Optional[models.Account]:
        """
        Retrieves an account by ID.

        Args:
            current_user: The current active user.
            account_id: The ID of the account to retrieve.

        Returns:
            Account: The retrieved account object.
        """

        logger.info("Getting account %s for user: %s", account_id, current_user.id)
        account = await self.repository.get(models.Account, account_id)

        if account is None:
            return None

        if self.has_user_access_to_account(current_user, account):
            logger.info("Found account %s for user: %s", account_id, current_user.id)
            return account

        return None

    async def create_account(
        self, user: models.User, account: schemas.Account
    ) -> models.Account:
        """
        Creates a new account.

        Args:
            user: The user object.
            account: The account data.

        Returns:
            Account: The created account object.
        """

        logger.info("Creating new account for user: %s", user.id)
        db_account = models.Account(user=user, **account.model_dump())
        await self.repository.save(db_account)
        logger.info("Account created for user: %s", user.id)
        return db_account

    async def update_account(
        self, current_user: models.User, account_id, account: schemas.AccountData
    ) -> Optional[models.Account]:
        """
        Updates an account.

        Args:
            current_user: The current active user.
            account_id: The ID of the account to update.
            account: The updated account data.

        Returns:
            Account: The updated account information.
        """

        logger.info("Updating account %s for user: %s", account_id, current_user.id)
        db_account = await self.repository.get(models.Account, account_id)

        if db_account is None:
            return None

        if db_account.user_id == current_user.id:
            await self.repository.update(
                models.Account, db_account.id, **account.model_dump()
            )
            logger.info("Account %s updated for user:  %s", account, current_user.id)
            return db_account
        logger.warning(
            "Account %s not found or does not belong to user: %s",
            account,
            current_user.id,
        )
        return None

    async def delete_account(
        self, current_user: models.User, account_id: int
    ) -> Optional[bool]:
        """
        Deletes an account.

        Args:
            current_user: The current active user.
            account_id: The ID of the account to delete.

        Returns:
            bool: True if the account is successfully deleted, False otherwise.
        """

        logger.info("Deleting account %s for user: %s", account_id, current_user.id)
        account = await self.repository.get(models.Account, account_id)
        if account and account.user_id == current_user.id:
            await self.repository.delete(account)
            logger.info("Account %s deleted for user: %s", account_id, current_user.id)
            return True
        logger.warning(
            "Account %s not found or does not belong to user: %s",
            account_id,
            current_user.id,
        )
        return None

    async def check_max_accounts(self, user: models.User) -> bool:
        """
        Checks if the maximum number of accounts has been reached for a user.

        Args:
            user: The user object.

        Returns:
            bool: True if the maximum number of accounts has been reached, False otherwise.
        """

        logger.info("Checking if maximum accounts reached for user: %s", user.id)
        account_list = await self.get_accounts(user)

        if account_list is None:
            return True

        result = len(account_list) >= settings.max_allowed_accounts
        if result:
            logger.warning(
                "User %s has reached the maximum allowed accounts limit.", user.id
            )
        return result

    @staticmethod
    def calculate_total_balance(account_list: list[models.Account]) -> float:
        """
        Calculates the total balance of a list of accounts.

        Args:
            account_list: A list of account objects.

        Returns:
            float: The total balance of the accounts.
        """

        return sum(account.balance for account in account_list)

    @staticmethod
    def has_user_access_to_account(user: models.User, account: models.Account) -> bool:
        """
        Check if the user has access to the account.

        Args:
            user: The user object.
            account: The account object.

        Returns:
            bool: True if the user has access to the account, False otherwise.
        """
        return user.id == account.user_id
