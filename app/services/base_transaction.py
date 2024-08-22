from typing import Optional, Type, Union

from app import models, schemas
from app.logger import get_logger
from app.repository import Repository
from app.services.base import BaseService
from app.services.wallets import WalletService
from app.utils.classes import RoundedDecimal
from app.utils.exceptions import (
    AccessDeniedException,
    TransactionNotFoundException,
    WalletNotFoundException,
)

logger = get_logger(__name__)


class BaseTransactionService(BaseService):
    def __init__(
        self,
        service_model: Type[Union[models.Transaction, models.TransactionScheduled]],
        repository: Optional[Repository] = None,
    ):
        self.service_model = service_model

        super().__init__(repository)

    async def _get_transaction_by_id(
        self, transaction_id: int
    ) -> Optional[Union[models.Transaction, models.TransactionScheduled]]:
        """
        Retrieves a transaction by ID.

        Args:
            transaction_id: The ID of the transaction to retrieve.

        Returns:
            The transaction if found, None otherwise.
        """
        if self.service_model is models.Transaction:
            return await self.repository.get(
                self.service_model,
                transaction_id,
                load_relationships_list=[self.service_model.offset_transaction],
            )

        return await self.repository.get(
            self.service_model,
            transaction_id,
        )

    async def get_transaction(
        self, user: models.User, transaction_id: int
    ) -> Optional[models.Transaction]:
        """
        Retrieves a transaction for a specific user by ID.

        Args:
            user: The user for whom the transaction is being retrieved.
            transaction_id: The ID of the transaction to retrieve.

        Returns:
            The transaction if found, None otherwise.

        Raises:
            TransactionNotFoundException: If the transaction does not exist.
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """
        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            raise TransactionNotFoundException(transaction_id)

        wallet = await self.repository.get(models.Wallet, transaction.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(transaction.wallet_id)

        if WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

        if wallet.user_id == user.id:
            logger.info("User ID verified. Returning transaction.")
            return transaction

        logger.warning(WALLET_USER_ID_MISMATCH)
        return None

    async def delete_transaction(
        self, current_user: models.User, transaction_id: int
    ) -> Optional[bool]:
        """
        Deletes a transaction for the current user by ID.

        Args:
            current_user: The current user performing the deletion.
            transaction_id: The ID of the transaction to delete.

        Returns:
            True if the transaction is successfully deleted, None otherwise.

        Raises:
            TransactionNotFoundException: If the transaction does not exist.
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            raise TransactionNotFoundException(transaction_id)

        wallet = await self.repository.get(models.Wallet, transaction.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(transaction.wallet_id)

        if WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

        amount = transaction.information.amount

        if transaction.offset_transaction:
            logger.info("Handling offset transaction for delete.")
            offset_transaction = transaction.offset_transaction
            offset_wallet = await self.repository.get(
                models.Wallet, offset_transaction.wallet_id
            )

            if offset_wallet is None:
                raise WalletNotFoundException(offset_transaction.wallet_id)

            offset_wallet.balance += amount
            await self.repository.delete(transaction.offset_transaction)

        wallet.balance -= amount
        await self.repository.delete(transaction)

        return True

    async def create_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        """
        Creates a new transaction for a user based on the provided transaction data.

        Args:
            user: The user for whom the transaction is being created.
            transaction_data: The data for the new transaction.

        Returns:
            The created transaction if successful, None otherwise.

        Raises:
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """
        wallet = await self.repository.get(models.Wallet, transaction_data.wallet_id)

        if wallet is None:
            raise WalletNotFoundException(wallet_id)

        if not WalletService.has_user_access_to_wallet(user, wallet):
            raise AccessDeniedException(user.id, wallet.id)

        db_transaction_information = models.TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_data.model_dump()
        )

        transaction = self.service_model(
            information=db_transaction_information,
            wallet_id=wallet.id,
            scheduled_transaction_id=transaction_data.scheduled_transaction_id,
        )

        if transaction_data.offset_wallet_id:
            logger.info("Handling offset wallet for transaction.")
            offset_transaction = await self._handle_offset_transaction(
                user, transaction_data
            )

            if offset_transaction is None:
                logger.warning(
                    "User[id: %s] not allowed to access offset_wallet[id: %s]",
                    user.id,
                    transaction_data.offset_wallet_id,
                )
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_wallet[id: {transaction_data.offset_wallet_id}]"
                    )
                )

            transaction.offset_transaction = offset_transaction
            offset_transaction.offset_transaction = transaction
            await self.repository.save(offset_transaction)

        wallet.balance += db_transaction_information.amount

        await self.repository.save([wallet, transaction, db_transaction_information])

        return transaction

    async def _handle_offset_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        """
        Handles the creation of an offset transaction for a user based on the provided data.

        Args:
            user: The user for whom the offset transaction is being handled.
            transaction_data: The data for the offset transaction.

        Returns:
            The created offset transaction if successful, None otherwise.

        Raises:
            ValueError: If offset_wallet_id in transaction_information does not exist.
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """
        logger.info("Handling offset transaction for user %s", user.id)
        offset_wallet_id = transaction_data.offset_wallet_id

        if offset_wallet_id is None:
            raise ValueError("No offset_wallet_id provided")

        offset_wallet = await self.repository.get(models.Wallet, offset_wallet_id)

        if offset_wallet is None:
            raise WalletNotFoundException(offset_wallet_id)

        if not WalletService.has_user_access_to_wallet(user, offset_wallet.id):
            raise AccessDeniedException(user.id, offset_wallet.id)

        transaction_data.amount = RoundedDecimal(transaction_data.amount * -1)
        offset_wallet.balance += transaction_data.amount

        db_offset_transaction_information = models.TransactionInformation()
        db_offset_transaction_information.add_attributes_from_dict(
            transaction_data.model_dump()
        )

        offset_transaction = self.service_model(
            information=db_offset_transaction_information,
            wallet_id=offset_wallet_id,
            scheduled_transaction_id=transaction_data.scheduled_transaction_id,
        )

        await self.repository.save(offset_transaction)

        return offset_transaction

    async def update_transaction(
        self,
        current_user: models.User,
        transaction_id: int,
        transaction_information: schemas.TransactionInformtionUpdate,
    ) -> Optional[models.Transaction]:
        """
        Updates a transaction for the current user by ID with the provided information.

        Args:
            current_user: The current user updating the transaction.
            transaction_id: The ID of the transaction to update.
            transaction_information: The updated information for the transaction.

        Returns:
            The updated transaction if successful, None otherwise.

        Raises:
            TransactionNotFoundException: If the transaction does not exist.
            WalletNotFoundException: If the wallet does not exist.
            AccessDeniedException: If the user does not have access to the wallet.
        """

        transaction = await self._get_transaction_by_id(transaction_id)

        if transaction is None:
            raise TransactionNotFoundException(transaction_id)

        wallet: models.Wallet = transaction.wallet

        if not WalletService.has_user_access_to_wallet(user, wallet.id):
            raise AccessDeniedException(user.id, wallet.id)

        amount_updated = (
            round(transaction_information.amount, 2) - transaction.information.amount
        )

        if transaction.offset_transactions_id:
            logger.info("Handling offset transaction for update.")
            offset_transaction = await self.repository.get(
                self.service_model,
                transaction.offset_transactions_id,
                load_relationships_list=[self.service_model.wallet],
            )

            if offset_transaction is None:
                raise TransactionNotFoundException(transaction.offset_transactions_id)

            offset_wallet: models.Wallet = offset_transaction.wallet

            if not WalletService.has_user_access_to_wallet(user, offset_wallet.id):
                raise AccessDeniedException(user.id, offset_wallet.id)

            offset_wallet.balance -= amount_updated
            offset_transaction.information.amount = transaction_information.amount * -1

        wallet_values = {"balance": wallet.balance + amount_updated}
        await self.repository.update(models.Wallet, wallet.id, **wallet_values)

        transaction_values = {
            "amount": transaction_information.amount,
            "reference": transaction_information.reference,
            "date": transaction_information.date,
            "category_id": transaction_information.category_id,
        }
        await self.repository.update(
            models.TransactionInformation,
            transaction.information.id,
            **transaction_values,
        )

        return transaction
