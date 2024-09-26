import asyncio
from typing import Optional

from app.models import Transaction, TransactionInformation, TransactionScheduled, User
from app.repository import Repository
from app.schemas import (
    ScheduledTransactionInformationCreate,
    ScheduledTransactionInformtionUpdate,
)
from app.services.base_transaction import BaseTransactionService
from app.services.category import CategoryService
from app.services.frequency import FrequencyService
from app.services.wallets import WalletService


class ScheduledTransactionService(BaseTransactionService):
    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(TransactionScheduled, repository)

    async def _get_scheduled_transaction_by_id(
        self, scheduled_transaction_id: int
    ) -> TransactionScheduled:
        """
        Retrieves a scheduled transaction by ID.

        Args:
            scheduled_transaction_id: The ID of the transaction to retrieve.

        Returns:
            The scheduled transaction if found, None otherwise.
        """

        return await self.repository.get(
            self.service_model,
            scheduled_transaction_id,
        )

    async def get_scheduled_transaction(
        self,
        user: User,
        transaction_id: int,
    ) -> TransactionScheduled:
        """
        Retrieves a transaction by its ID.

        Args:
            user: The user for whom the transaction is being retrieved.
            transaction_id: The ID of the transaction to retrieve.

        Returns:
            The transaction with the specified ID.
        """

        scheduled_transaction = await self._get_scheduled_transaction_by_id(
            transaction_id
        )

        await self.wallet_service.validate_access_to_wallet(
            user, scheduled_transaction.wallet_id
        )

        return scheduled_transaction

    async def get_scheduled_transaction_list(
        self,
        user: User,
        wallet_id: int,
    ) -> list[TransactionScheduled]:
        """
        Retrieves a list of transactions for a specific user and wallet.

        Args:
            user: The user for whom transactions are being retrieved.
            wallet_id: The ID of the wallet for which transactions are being retrieved.

        Returns:
            A list of transactions that match the criteria.
        """

        wallet = await WalletService().get_wallet(user, wallet_id)

        return await self.repository.filter_by(
            self.service_model,
            self.service_model.wallet_id,
            wallet.id,
        )

    async def create_scheduled_transaction(
        self,
        user: User,
        transaction_information: ScheduledTransactionInformationCreate,
    ) -> TransactionScheduled:
        """
        Creates a new scheduled transaction for a user based on the provided information.

        Args:
            user: The user for whom the scheduled transaction is being created.
            transaction_information: The information for the new scheduled transaction.

        Returns:
            The created scheduled transaction if successful, None otherwise.
        """
        wallet_id = transaction_information.wallet_id
        wallet = await self.wallet_service.get_wallet(user, wallet_id)

        category = await CategoryService().get_category(
            user, transaction_information.category_id
        )

        frequency = await FrequencyService().get_frequency(
            transaction_information.frequency_id
        )

        db_transaction_information = TransactionInformation(
            amount=transaction_information.amount,
            reference=transaction_information.reference,
            category=category,
            category_id=category.id,
        )

        offset_wallet_id = transaction_information.offset_wallet_id
        transaction = self.service_model(
            frequency_id=transaction_information.frequency_id,
            frequency=frequency,
            date_start=transaction_information.date_start,
            date_end=transaction_information.date_end,
            information=db_transaction_information,
            wallet_id=wallet.id,
            offset_wallet_id=offset_wallet_id,
        )

        if transaction_information.offset_wallet_id:
            await self.wallet_service.validate_access_to_wallet(user, offset_wallet_id)

        await self.repository.save([transaction, db_transaction_information])

        return transaction

    async def update_scheduled_transaction(
        self,
        user: User,
        transaction_id: int,
        transaction_information: ScheduledTransactionInformtionUpdate,
    ) -> TransactionScheduled:
        """
        Updates a scheduled transaction for a user with the provided information.

        Args:
            user: The user for whom the scheduled transaction is being updated.
            transaction_id: The ID of the scheduled transaction to update.
            transaction_information: The updated information for the scheduled transaction.

        Returns:
            The updated scheduled transaction if successful, None otherwise.
        """

        transaction = await self._get_scheduled_transaction_by_id(transaction_id)

        await self.wallet_service.validate_access_to_wallet(user, transaction.wallet_id)

        if transaction.offset_wallet_id and transaction_information.offset_wallet_id:
            offset_wallet_id = transaction_information.offset_wallet_id
            await self.wallet_service.validate_access_to_wallet(user, offset_wallet_id)

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
        self, user: User, transaction_id: int
    ) -> bool:
        """
        Deletes a scheduled transaction.

        Args:
            user: The current active user.
            transaction_id: The ID of the scheduled transaction to delete.

        Returns:
            bool: True if the scheduled transaction is successfully deleted, False otherwise.
        """

        transaction = await self._get_scheduled_transaction_by_id(transaction_id)

        await self.wallet_service.validate_access_to_wallet(user, transaction.wallet_id)

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
