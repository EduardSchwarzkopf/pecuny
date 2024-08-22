import asyncio
from typing import Optional

from app.logger import get_logger
from app.models import (
    Transaction,
    TransactionInformation,
    TransactionScheduled,
    User,
    Wallet,
)
from app.repository import Repository
from app.schemas import (
    ScheduledTransactionInformationCreate,
    ScheduledTransactionInformtionUpdate,
)
from app.services.base_transaction import BaseTransactionService
from app.services.wallets import WalletService
from app.utils.exceptions import (
    AccessDeniedException,
    TransactionNotFoundException,
    WalletNotFoundException,
)

logger = get_logger(__name__)

ServiceModel = TransactionScheduled


class ScheduledTransactionService(BaseTransactionService):
    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(ServiceModel, repository)

    async def get_transaction_list(
        self,
        user: User,
        wallet_id: int,
    ) -> list[ServiceModel]:
        """
        Retrieves a list of transactions for a specific user and wallet.

        Args:
            user: The user for whom transactions are being retrieved.
            wallet_id: The ID of the wallet for which transactions are being retrieved.

        Returns:
            A list of transactions that match the criteria.
        """
        logger.info(
            "Starting transaction list retrieval for user %s and wallet %s",
            user.id,
            wallet_id,
        )
        wallet = await self.repository.get(Wallet, wallet_id)

        if wallet is None:
            return []

        if wallet is None or not WalletService.has_user_access_to_wallet(user, wallet):
            return []

        return await self.repository.filter_by(
            self.service_model,
            self.service_model.wallet_id,
            wallet.id,
        )

    async def create_scheduled_transaction(
        self,
        user: User,
        transaction_information: ScheduledTransactionInformationCreate,
    ) -> Optional[ServiceModel]:
        """
        Creates a new scheduled transaction for a user based on the provided information.

        Args:
            user: The user for whom the scheduled transaction is being created.
            transaction_information: The information for the new scheduled transaction.

        Returns:
            The created scheduled transaction if successful, None otherwise.
        """
        logger.info("Creating new scheduled transaction for user %s", user.id)
        wallet = await self.repository.get(Wallet, transaction_information.wallet_id)

        if wallet is None or not WalletService.has_user_access_to_wallet(user, wallet):
            return None

        db_transaction_information = TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )

        transaction = self.service_model(
            frequency_id=transaction_information.frequency_id,
            date_start=transaction_information.date_start,
            date_end=transaction_information.date_end,
            information=db_transaction_information,
            wallet_id=wallet.id,
            offset_wallet_id=transaction_information.offset_wallet_id,
        )

        if transaction_information.offset_wallet_id:
            offset_wallet = await self.repository.get(
                Wallet, transaction_information.offset_wallet_id
            )

            if offset_wallet is None or not WalletService.has_user_access_to_wallet(
                user, offset_wallet
            ):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_wallet[id: {transaction_information.offset_wallet_id}]"
                    )
                )

        await self.repository.save([transaction, db_transaction_information])

        return transaction

    async def update_scheduled_transaction(
        self,
        user: User,
        transaction_id: int,
        transaction_information: ScheduledTransactionInformtionUpdate,
    ) -> Optional[ServiceModel]:
        """
        Updates a scheduled transaction for a user with the provided information.

        Args:
            user: The user for whom the scheduled transaction is being updated.
            transaction_id: The ID of the scheduled transaction to update.
            transaction_information: The updated information for the scheduled transaction.

        Returns:
            The updated scheduled transaction if successful, None otherwise.
        """

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            return None

        wallet = await self.repository.get(Wallet, transaction_information.wallet_id)
        if wallet is None or not WalletService.has_user_access_to_wallet(user, wallet):
            return None

        if transaction.offset_wallet_id and transaction_information.offset_wallet_id:
            offset_wallet = await self.repository.get(
                Wallet, transaction_information.offset_wallet_id
            )

            if offset_wallet is None or not WalletService.has_user_access_to_wallet(
                user, offset_wallet
            ):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_wallet[id: {transaction_information.offset_wallet_id}]"
                    )
                )

        transaction_values = {
            "amount": transaction_information.amount,
            "reference": transaction_information.reference,
            "category_id": transaction_information.category_id,
        }

        await self.repository.update(
            TransactionInformation,
            transaction.information.id,
            **transaction_values,
        )

        transaction.add_attributes_from_dict(transaction_information.model_dump())
        await self.repository.save(transaction)

        return transaction

    async def delete_scheduled_transaction(
        self, current_user: User, transaction_id: int
    ) -> Optional[bool]:
        """
        Deletes a scheduled transaction.

        Args:
            current_user: The current active user.
            transaction_id: The ID of the scheduled transaction to delete.

        Returns:
            bool: True if the scheduled transaction is successfully deleted, False otherwise.
        """

        logger.info(
            "Deleting scheduled_transaction with ID %s for user %s",
            transaction_id,
            current_user.id,
        )

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            logger.warning(
                "Scheduled Transaction with ID %s not found.", transaction_id
            )
            return None

        wallet = await self.repository.get(Wallet, transaction.wallet_id)
        if wallet is None or current_user.id != wallet.user_id:
            return None

        created_transaction_list = await self.repository.filter_by(
            Transaction,
            Transaction.scheduled_transaction_id,
            transaction.id,
        )

        if len(created_transaction_list) > 0:

            async def update_transaction(transaction):
                transaction.scheduled_transaction_id = None

            update_tasks = [update_transaction(tx) for tx in created_transaction_list]
            await asyncio.gather(*update_tasks)

            await self.repository.save(created_transaction_list)

        await self.repository.delete(transaction)

        return True
