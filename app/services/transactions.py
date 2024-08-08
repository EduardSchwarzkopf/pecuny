from datetime import datetime
from typing import List, Optional

from app import models, schemas
from app.logger import get_logger
from app.repository import Repository
from app.services.accounts import AccountService
from app.services.base_transaction import BaseTransactionService

logger = get_logger(__name__)


class TransactionService(
    BaseTransactionService,
):
    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(models.Transaction, repository)

    async def get_transaction_list(
        self,
        user: models.User,
        account_id: int,
        date_start: datetime,
        date_end: datetime,
    ) -> List[models.Transaction]:
        """
        Retrieves a list of transactions for a specific user and account within a given date range.

        Args:
            user: The user for whom transactions are being retrieved.
            account_id: The ID of the account for which transactions are being retrieved.
            date_start: Optional start date for filtering transactions.
            date_end: Optional end date for filtering transactions.

        Returns:
            A list of transactions that match the criteria.
        """
        logger.info(
            "Starting transaction list retrieval for user %s and account %s",
            user.id,
            account_id,
        )
        account = await self.repository.get(models.Account, account_id)

        if account and AccountService.has_user_access_to_account(user, account):
            return []

        return await self.repository.get_transactions_from_period(
            account_id, date_start, date_end
        )

    async def get_transaction(
        self, user: models.User, transaction_id: int
    ) -> Optional[models.Transaction]:
        """
        Retrieves a transaction by ID.

        Args:
            user: The user object.
            transaction_id: The ID of the transaction to retrieve.

        Returns:
            Transaction: The retrieved transaction.

        Raises:
            None
        """

        return await super().get_transaction(user, transaction_id)

    async def create_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        """
        Creates a new transaction.

        Args:
            user: The user object.
            transaction_information: The information for the transaction.

        Returns:
            Transaction: The created transaction.

        Raises:
            None
        """
        return await super().create_transaction(user, transaction_data)

    async def _handle_offset_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        """
        Handles an offset transaction for a user.

        Args:
            user: The user object.
            transaction_information: The information for the offset transaction.

        Returns:
            Transaction: The created offset transaction.

        Raises:
            None
        """
        return await super()._handle_offset_transaction(user, transaction_data)

    async def update_transaction(
        self,
        current_user: models.User,
        transaction_id: int,
        transaction_information: schemas.TransactionInformtionUpdate,
    ) -> Optional[models.Transaction]:
        """
        Updates a transaction.

        Args:
            current_user: The current active user.
            transaction_id: The ID of the transaction to update.
            transaction_information: The updated transaction information.

        Returns:
            Transaction: The updated transaction.

        Raises:
            None
        """
        return await super().update_transaction(
            current_user, transaction_id, transaction_information
        )

    async def delete_transaction(
        self, current_user: models.User, transaction_id: int
    ) -> Optional[bool]:
        """
        Deletes a transaction.

        Args:
            current_user: The current active user.
            transaction_id: The ID of the transaction to delete.

        Returns:
            bool: True if the transaction is successfully deleted, False otherwise.
        """
        return await super().delete_transaction(current_user, transaction_id)
