import asyncio
from typing import Optional

from app.logger import get_logger
from app.models import (
    Account,
    Transaction,
    TransactionInformation,
    TransactionScheduled,
    User,
)
from app.repository import Repository
from app.schemas import (
    ScheduledTransactionInformationCreate,
    ScheduledTransactionInformtionUpdate,
)
from app.services.accounts import AccountService
from app.services.base_transaction import BaseTransactionService
from app.utils.exceptions import AccessDeniedError
from app.utils.log_messages import ACCOUNT_USER_ID_MISMATCH

logger = get_logger(__name__)

ServiceModel = TransactionScheduled


class ScheduledTransactionService(BaseTransactionService):
    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(TransactionScheduled)

    async def get_transaction_list(
        self,
        user: User,
        account_id: int,
        """
        Retrieves a list of transactions for a specific user and account.

        Args:
            user: The user for whom transactions are being retrieved.
            account_id: The ID of the account for which transactions are being retrieved.

        Returns:
            A list of transactions that match the criteria.
        """
        logger.info(

    async def create_scheduled_transaction(
        self,
        user: User,
        transaction_information: ScheduledTransactionInformationCreate,
        """
        Creates a new scheduled transaction for a user based on the provided information.

        Args:
            user: The user for whom the scheduled transaction is being created.
            transaction_information: The information for the new scheduled transaction.

        Returns:
            The created scheduled transaction if successful, None otherwise.
        """
        logger.info("Creating new scheduled transaction for user %s", user.id)
        account = await self.repository.get(Account, transaction_information.account_id)

        if account is None or not AccountService.has_user_access_to_account(
            user, account
        ):
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
            account_id=account.id,
            offset_account_id=transaction_information.offset_account_id,
        )

        if transaction_information.offset_account_id:
            offset_account = await self.repository.get(
                Account, transaction_information.offset_account_id
            )

            if offset_account is None or not AccountService.has_user_access_to_account(
                user, offset_account
            ):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_information.offset_account_id}]"
                    )
                )

        await self.repository.save([transaction, db_transaction_information])

        return transaction

    async def update_scheduled_transaction(
        self,
        user: User,
        transaction_id: int,
        transaction_information: ScheduledTransactionInformtionUpdate,
        """
        Updates a scheduled transaction for a user with the provided information.

        Args:
            user: The user for whom the scheduled transaction is being updated.
            transaction_id: The ID of the scheduled transaction to update.
            transaction_information: The updated information for the scheduled transaction.

        Returns:
            The updated scheduled transaction if successful, None otherwise.
        """

        if transaction is None:
            return None

        account = await self.repository.get(Account, transaction_information.account_id)
        if (
            transaction is None
            or account is None
            or not AccountService.has_user_access_to_account(user, account)
        ):
            return None

        if transaction.offset_account_id:
            offset_account = await self.repository.get(
                Account, transaction_information.offset_account_id
            )

            if offset_account is None or not AccountService.has_user_access_to_account(
                user, offset_account
            ):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_information.offset_account_id}]"
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

        transaction = await self.repository.get(self.service_model, transaction_id)

        if transaction is None:
            logger.warning(
                "Scheduled Transaction with ID %s not found.", transaction_id
            )
            return None

        account = await self.repository.get(Account, transaction.account_id)
        if account is None or current_user.id != account.user_id:
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
