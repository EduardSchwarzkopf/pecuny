from typing import Optional

from app import models, schemas
from app.logger import get_logger
from app.services.accounts import AccountService
from app.services.base import BaseService
from app.utils.exceptions import AccessDeniedError

logger = get_logger(__name__)


class ScheduledTransactionService(BaseService):
    async def get_transaction_list(
        self,
        user: models.User,
        account_id: int,
    ) -> list[Optional[models.TransactionScheduled]]:
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

        account = await self.repository.get(models.Account, account_id)

        if account is None:
            return []

        if account.user_id == user.id:
            return await self.repository.filter_by(
                models.TransactionScheduled,
                models.TransactionScheduled.account_id,
                account.id,
            )

        return []

    async def get_transaction(
        self, user: models.User, transaction_id: int
    ) -> Optional[models.TransactionScheduled]:
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

        transaction = await self.repository.get(
            models.TransactionScheduled, transaction_id
        )

        if transaction is None:
            return None

        account = await self.repository.get(models.Account, transaction.account_id)

        if account is None:
            return None

        return transaction if account.user_id == user.id else None

    async def create_scheduled_transaction(
        self,
        user: models.User,
        transaction_information: schemas.ScheduledTransactionInformationCreate,
    ) -> Optional[models.TransactionScheduled]:
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

        account = await self.repository.get(
            models.Account, transaction_information.account_id
        )

        if account is None:
            return None

        if not AccountService.has_user_access_to_account(  # pylint: disable=duplicate-code
            user, account
        ):
            return None

        offset_account_id = transaction_information.offset_account_id

        if offset_account_id:
            offset_account = await self.repository.get(
                models.Account, offset_account_id
            )

            if offset_account is None:
                return None

            if not AccountService.has_user_access_to_account(user, offset_account):
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_information.offset_account_id}]"
                    )
                )

        db_transaction_information = models.TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )

        transaction = models.TransactionScheduled(
            frequency_id=transaction_information.frequency_id,
            date_start=transaction_information.date_start,
            date_end=transaction_information.date_end,
            information=db_transaction_information,
            account_id=account.id,
            offset_account_id=offset_account_id,
        )

        await self.repository.save([transaction, db_transaction_information])

        return transaction

    async def delete_scheduled_transaction(
        self, current_user: models.User, transaction_id: int
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
            models.TransactionScheduled,
            transaction_id,
        )

        if transaction is None:
            logger.warning(
                "Scheduled Transaction with ID %s not found.", transaction_id
            )
            return None

        account = await self.repository.get(models.Account, transaction.account_id)
        if account is None or current_user.id != account.user_id:
            return None

        created_transaction_list = await self.repository.filter_by(
            models.Transaction,
            models.Transaction.scheduled_transaction_id,
            transaction.id,
        )

        # TODO: add user decision to delete created transaction or not
        for created_transaction in created_transaction_list:
            created_transaction.scheduled_transaction_id = None

        self.repository.save(created_transaction_list)

        await self.repository.delete(transaction)

        return True
