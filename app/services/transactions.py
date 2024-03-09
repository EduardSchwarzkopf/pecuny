from datetime import datetime
from typing import List

from app import models
from app import repository as repo
from app import schemas
from app.logger import get_logger
from app.utils.account_utils import has_user_access_to_account
from app.utils.exceptions import AccessDeniedError
from app.utils.log_messages import ACCOUNT_USER_ID_MISMATCH

logger = get_logger(__name__)


class TransactionService:
    """
    A service for managing transactions.

    Args:
        self: The instance of the TransactionService class.

    """

    async def get_transaction_list(
        self,
        user: models.User,
        account_id: int,
        date_start: datetime,
        date_end: datetime,
    ) -> List[models.Transaction]:
        """
        Retrieves a list of transactions within a specified period for a given account.

        Args:
            user: The user object.
            account_id: The ID of the account.
            date_start: The start date of the period.
            date_end: The end date of the period.

        Returns:
            List[Transaction]: A list of transactions within the specified period.

        Raises:
            None
        """

        logger.info(
            "Starting transaction list retrieval for user %s and account %s",
            user.id,
            account_id,
        )
        account = await repo.get(models.Account, account_id)
        if account.user_id == user.id:
            logger.info("User ID verified. Retrieving transactions.")
            return await repo.get_transactions_from_period(
                account_id, date_start, date_end
            )

        logger.warning(ACCOUNT_USER_ID_MISMATCH)

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

        logger.info(
            "Retrieving transaction with ID %s for user %s", transaction_id, user.id
        )
        transaction = await repo.get(models.Transaction, transaction_id)

        if transaction is None:
            logger.warning("Transaction with ID %s not found.", transaction_id)
            return

        account = await repo.get(models.Account, transaction.account_id)

        if account.user_id == user.id:
            logger.info("User ID verified. Returning transaction.")
            return transaction

        logger.warning(ACCOUNT_USER_ID_MISMATCH)

    async def create_transaction(
        self,
        user: models.User,
        transaction_information: schemas.TransactionInformationCreate,
    ) -> models.Transaction:
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

        logger.info("Creating new transaction for user %s", user.id)
        account = await repo.get(models.Account, transaction_information.account_id)

        if not has_user_access_to_account(user, account):
            logger.warning(ACCOUNT_USER_ID_MISMATCH)
            return None

        db_transaction_information = models.TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )

        transaction = models.Transaction(
            information=db_transaction_information, account_id=account.id
        )

        if transaction_information.offset_account_id:
            logger.info("Handling offset account for transaction.")
            offset_transaction = await self._handle_offset_transaction(
                user, transaction_information
            )

            if offset_transaction is None:
                logger.warning(
                    "User[id: %s] not allowed to access offset_account[id: %s]",
                    user.id,
                    transaction_information.offset_account_id,
                )
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_information.offset_account_id}]"
                    )
                )

            transaction.offset_transaction = offset_transaction
            offset_transaction.offset_transaction = transaction
            await repo.save(offset_transaction)

        account.balance += db_transaction_information.amount

        await repo.save([account, transaction, db_transaction_information])

        return transaction

    async def _handle_offset_transaction(
        self,
        user: models.User,
        transaction_information: schemas.TransactionInformationCreate,
    ) -> models.Transaction:
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

        logger.info("Handling offset transaction for user %s", user.id)
        offset_account_id = transaction_information.offset_account_id
        offset_account = await repo.get(models.Account, offset_account_id)

        if user.id != offset_account.user_id:
            logger.warning("User ID does not match the offset account's User ID.")
            return None

        transaction_information.amount = transaction_information.amount * -1
        offset_account.balance += transaction_information.amount

        db_offset_transaction_information = models.TransactionInformation()
        db_offset_transaction_information.add_attributes_from_dict(
            transaction_information.model_dump()
        )
        offset_transaction = models.Transaction(
            information=db_offset_transaction_information,
            account_id=offset_account_id,
        )

        await repo.save(offset_transaction)

        return offset_transaction

    async def update_transaction(
        self,
        current_user: models.User,
        transaction_id: int,
        transaction_information: schemas.TransactionInformtionUpdate,
    ):
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

        logger.info(
            "Updating transaction with ID %s for user %s",
            transaction_id,
            current_user.id,
        )
        transaction = await repo.get(models.Transaction, transaction_id)
        if transaction is None:
            logger.warning("Transaction with ID %s not found.", transaction_id)
            return

        account = await repo.get(models.Account, transaction.account_id)
        if current_user.id != account.user_id:
            logger.warning(ACCOUNT_USER_ID_MISMATCH)
            return

        amount_updated = (
            round(transaction_information.amount, 2) - transaction.information.amount
        )

        if transaction.offset_transactions_id:
            logger.info("Handling offset transaction for update.")
            offset_transaction = await repo.get(
                models.Transaction, transaction.offset_transactions_id
            )
            offset_account = await repo.get(
                models.Account, offset_transaction.account_id
            )

            if offset_account.user_id != current_user.id:
                logger.warning("User ID does not match the offset account's User ID.")
                return

            offset_account.balance -= amount_updated
            offset_transaction.information.amount = transaction_information.amount * -1

        account_values = {"balance": account.balance + amount_updated}

        await repo.update(models.Account, account.id, **account_values)

        transaction_values = {
            "amount": transaction_information.amount,
            "reference": transaction_information.reference,
            "date": transaction_information.date,
            "category_id": transaction_information.category_id,
        }

        await repo.update(
            models.TransactionInformation,
            transaction.information.id,
            **transaction_values,
        )

        return transaction

    async def delete_transaction(
        self, current_user: models.User, transaction_id: int
    ) -> bool:
        """
        Deletes a transaction.

        Args:
            current_user: The current active user.
            transaction_id: The ID of the transaction to delete.

        Returns:
            bool: True if the transaction is successfully deleted, False otherwise.
        """

        logger.info(
            "Deleting transaction with ID %s for user %s",
            transaction_id,
            current_user.id,
        )
        transaction = await repo.get(
            models.Transaction,
            transaction_id,
            load_relationships_list=[models.Transaction.offset_transaction],
        )

        if transaction is None:
            logger.warning("Transaction with ID %s not found.", transaction_id)
            return

        account = await repo.get(models.Account, transaction.account_id)
        if current_user.id != account.user_id:
            return

        amount = transaction.information.amount
        account.balance -= amount

        if transaction.offset_transaction:
            logger.info("Handling offset transaction for delete.")
            offset_transaction = transaction.offset_transaction
            offset_account = await repo.get(
                models.Account, offset_transaction.account_id
            )
            offset_account.balance += amount
            await repo.delete(transaction.offset_transaction)

        await repo.delete(transaction)

        return True
