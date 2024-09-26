from typing import Optional, Type, Union

from app import models, schemas
from app.repository import Repository
from app.services.base import BaseService
from app.services.wallets import WalletService
from app.utils.classes import RoundedDecimal


class BaseTransactionService(BaseService):
    def __init__(
        self,
        service_model: Type[Union[models.Transaction, models.TransactionScheduled]],
        repository: Optional[Repository] = None,
    ):
        self.service_model = service_model
        self.wallet_service = WalletService(repository)
        super().__init__(repository)

    async def __get_transaction_by_id(self, transaction_id: int):
        """
        Retrieves a transaction by ID.

        Args:
            transaction_id: The ID of the transaction to retrieve.

        Returns:
            The transaction if found, None otherwise.
        """

        return await self.repository.get(
            self.service_model,
            transaction_id,
            load_relationships_list=[self.service_model.offset_transaction],
        )

    async def delete_transaction(self, user: models.User, transaction_id: int) -> True:
        """
        Deletes a transaction for the current user by ID.

        Args:
            user: The current user performing the deletion.
            transaction_id: The ID of the transaction to delete.

        Returns:
            True if the transaction is successfully deleted, None otherwise.

        """

        transaction = await self.__get_transaction_by_id(transaction_id)

        wallet = await self.wallet_service.get_wallet(user, transaction.wallet_id)

        amount = transaction.information.amount

        if transaction.offset_transaction:
            offset_transaction = transaction.offset_transaction
            offset_wallet = await self.wallet_service.get_wallet(
                user, offset_transaction.wallet_id
            )

            offset_wallet.balance += amount
            await self.repository.delete(transaction.offset_transaction)

        wallet.balance -= amount
        await self.repository.delete(transaction)

        return True

    async def create_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> models.Transaction:
        """
        Creates a new transaction for a user based on the provided transaction data.

        Args:
            user: The user for whom the transaction is being created.
            transaction_data: The data for the new transaction.

        Returns:
            The created transaction if successful, None otherwise.

        """
        wallet = await self.wallet_service.get_wallet(user, transaction_data.wallet_id)

        category = await CategoryService().get_category(
            user, transaction_data.category_id
        )

        db_transaction_information = models.TransactionInformation(
            amount=transaction_data.amount,
            reference=transaction_data.reference,
            date=transaction_data.date,
            category=category,
            category_id=category.id,
        )

        transaction = self.service_model(
            information=db_transaction_information,
            wallet_id=wallet.id,
            scheduled_transaction_id=transaction_data.scheduled_transaction_id,
        )

        if transaction_data.offset_wallet_id:
            offset_transaction = await self._handle_offset_transaction(
                user, transaction_data
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
    ) -> models.Transaction:
        """
        Handles the creation of an offset transaction for a user based on the provided data.

        Args:
            user: The user for whom the offset transaction is being handled.
            transaction_data: The data for the offset transaction.

        Returns:
            The created offset transaction if successful, None otherwise.

        """
        offset_wallet_id = transaction_data.offset_wallet_id

        if offset_wallet_id is None:
            raise ValueError("No offset_wallet_id provided")

        offset_wallet = await self.wallet_service.get_wallet(user, offset_wallet_id)

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
        user: models.User,
        transaction_id: int,
        transaction_information: schemas.TransactionInformtionUpdate,
    ) -> models.Transaction:
        """
        Updates a transaction for the current user by ID with the provided information.

        Args:
            current_user: The current user updating the transaction.
            transaction_id: The ID of the transaction to update.
            transaction_information: The updated information for the transaction.

        Returns:
            The updated transaction if successful, None otherwise.
        """

        transaction = await self.__get_transaction_by_id(transaction_id)

        wallet = await self.wallet_service.get_wallet(user, transaction.wallet_id)

        amount_updated = (
            round(transaction_information.amount, 2) - transaction.information.amount
        )

            offset_wallet = await self.wallet_service.get_wallet(
                user, offset_transaction.wallet_id
            )

            offset_wallet.balance -= amount_updated
            offset_transaction.information.amount = transaction_information.amount * -1

        wallet_data = schemas.WalletData(**wallet.__dict__)
        wallet_data.balance = wallet.balance + amount_updated
        await self.wallet_service.update_wallet(user, wallet.id, wallet_data)

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
