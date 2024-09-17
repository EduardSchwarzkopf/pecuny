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


class ScheduledTransactionService(BaseTransactionService):
    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(TransactionScheduled, repository)

    async def get_transaction_list(
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

        Raises:
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """

        wallet = await self.repository.get(Wallet, wallet_id)

        if wallet is None:
            raise WalletNotFoundException(wallet_id)

        if not WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

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

        Raises:
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """
        wallet_id = transaction_information.wallet_id
        wallet = await self.repository.get(Wallet, transaction_information.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(wallet_id)

        if not WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

        db_transaction_information = TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )

        offset_wallet_id = transaction_information.offset_wallet_id
        transaction = self.service_model(
            frequency_id=transaction_information.frequency_id,
            date_start=transaction_information.date_start,
            date_end=transaction_information.date_end,
            information=db_transaction_information,
            wallet_id=wallet.id,
            offset_wallet_id=offset_wallet_id,
        )

        if transaction_information.offset_wallet_id:
            offset_wallet = await self.repository.get(Wallet, offset_wallet_id)

            if offset_wallet is None:
                raise WalletNotFoundException(offset_wallet_id)

            if not WalletService.has_user_access_to_wallet(user, offset_wallet):
                raise AccessDeniedException(user.id, offset_wallet.id)

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

        Raises:
            WalletNotFoundException: If the wallet does not exist.
            TransactionNotFoundException: If the transaction does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            raise TransactionNotFoundException(transaction_id)

        wallet = await self.repository.get(Wallet, transaction_information.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(wallet_id)

        if not WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

        if transaction.offset_wallet_id and transaction_information.offset_wallet_id:
            offset_wallet_id = transaction_information.offset_wallet_id
            offset_wallet = await self.repository.get(Wallet, offset_wallet_id)

            if offset_wallet is None:
                raise WalletNotFoundException(offset_wallet_id)

            if not WalletService.has_user_access_to_wallet(user, offset_wallet):
                raise AccessDeniedException(user.id, offset_wallet.id)

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

        Raises:
            WalletNotFoundException: If the wallet does not exist.
            TransactionNotFoundException: If the transaction does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            raise TransactionNotFoundException(transaction_id)

        wallet = await self.repository.get(Wallet, transaction.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(wallet_id)

        if not WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

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
