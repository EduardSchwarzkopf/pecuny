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
from app.schemas import (
    ScheduledTransactionInformationCreate,
    ScheduledTransactionInformtionUpdate,
)
from app.services.accounts import AccountService
from app.services.base import BaseService
from app.utils.exceptions import AccessDeniedError
from app.utils.log_messages import ACCOUNT_USER_ID_MISMATCH

logger = get_logger(__name__)

SERVICE_MODEL = TransactionScheduled


class ScheduledTransactionService(BaseService):

    async def get_transaction_list(
        self,
        user: User,
        account_id: int,
    ) -> list[Optional[SERVICE_MODEL]]:
        """
        Retrieves a list of transactions within a specified period for a given account.

        Args:
            user: The user object.
            account_id: The ID of the account.
            date_start: The start date of the period.
            date_end: The end date of the period.

        Returns:
            list[Transaction]: A list of transactions within the specified period.

        Raises:
            None
        """

        account = await self.repository.get(Account, account_id)

        if account is None:
            return []

        if account.user_id == user.id:
            return await self.repository.filter_by(
                SERVICE_MODEL,
                SERVICE_MODEL.account_id,
                account.id,
            )

        return []

    async def get_transaction(
        self, user: User, transaction_id: int
    ) -> Optional[SERVICE_MODEL]:
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

        transaction = await self.repository.get(SERVICE_MODEL, transaction_id)

        if transaction is None:
            return None

        account = await self.repository.get(Account, transaction.account_id)

        if account is None:
            return None

        return transaction if account.user_id == user.id else None

    async def create_scheduled_transaction(
        self,
        user: User,
        transaction_information: ScheduledTransactionInformationCreate,
    ) -> Optional[SERVICE_MODEL]:
        """
        Creates a scheduled transaction.

        Args:
            user: The user object.
            transaction_information: The information for the scheduled transaction.

        Returns:
            TransactionScheduled: The created scheduled transaction.

        Raises:
            None
        """

        account = await self.repository.get(Account, transaction_information.account_id)

        if account is None:
            return None

        if not AccountService.has_user_access_to_account(  # pylint: disable=duplicate-code
            user, account
        ):
            return None

        offset_account_id = transaction_information.offset_account_id

        if offset_account_id:
            offset_account = await self.repository.get(Account, offset_account_id)

            if offset_account is None:
                return None

            if not AccountService.has_user_access_to_account(user, offset_account):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_information.offset_account_id}]"
                    )
                )

        db_transaction_information = TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )

        transaction = SERVICE_MODEL(
            frequency_id=transaction_information.frequency_id,
            date_start=transaction_information.date_start,
            date_end=transaction_information.date_end,
            information=db_transaction_information,
            account_id=account.id,
            offset_account_id=offset_account_id,
        )

        await self.repository.save([transaction, db_transaction_information])

        return transaction

    async def update_scheduled_transaction(
        self,
        user: User,
        transaction_id: int,
        transaction_information: ScheduledTransactionInformtionUpdate,
    ) -> Optional[SERVICE_MODEL]:

        transaction = await self.repository.get(
            SERVICE_MODEL,
            transaction_id,
            load_relationships_list=[SERVICE_MODEL.account],
        )

        if transaction is None:
            return None

        account = await self.repository.get(Account, transaction_information.account_id)

        if not AccountService.has_user_access_to_account(  # pylint: disable=duplicate-code
            user, account
        ):
            return None

        if user.id != account.user_id:
            logger.warning(ACCOUNT_USER_ID_MISMATCH)
            return None

        offset_account_id = transaction_information.offset_account_id

        if transaction.offset_account_id:

            offset_account = await self.repository.get(Account, offset_account_id)

            if offset_account is None:
                return None

            if not AccountService.has_user_access_to_account(user, offset_account):
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

        transaction = await self.repository.get(
            SERVICE_MODEL,
            transaction_id,
        )

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
            # TODO: add user decision to delete created transaction or not
            async def update_transaction(transaction):
                transaction.scheduled_transaction_id = None

            update_tasks = [update_transaction(tx) for tx in created_transaction_list]
            await asyncio.gather(*update_tasks)

            # Save the updated transactions
            await self.repository.save(created_transaction_list)

        await self.repository.delete(transaction)

        return True
