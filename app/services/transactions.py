from datetime import datetime
from typing import List

from app import models
from app.services.base_transaction import BaseTransactionService


class TransactionService(BaseTransactionService):
    def __init__(self):
        super().__init__(models.Transaction)

    async def __get_transaction_by_id(self, transaction_id: int):
        return await self.repository.get(
            self.service_model,
            transaction_id,
            load_relationships_list=[self.service_model.offset_transaction],
        )

    async def get_transaction_list(
        self,
        user: models.User,
        wallet_id: int,
        date_start: datetime,
        date_end: datetime,
    ) -> List[models.Transaction]:
        """
        Retrieves a list of transactions for a specific user and wallet within a given date range.

        Args:
            user: The user for whom transactions are being retrieved.
            wallet_id: The ID of the wallet for which transactions are being retrieved.
            date_start: Optional start date for filtering transactions.
            date_end: Optional end date for filtering transactions.

        Returns:
            A list of transactions that match the criteria.
        """
        await self.wallet_service.validate_access_to_wallet(user, wallet_id)

        return await self.repository.get_transactions_from_period(
            wallet_id, date_start, date_end
        )

    async def get_transaction(
        self, user: models.User, transaction_id: int
    ) -> models.Transaction:
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

        transaction = await self.__get_transaction_by_id(transaction_id)

        await self.wallet_service.validate_access_to_wallet(user, transaction.wallet_id)

        return transaction
