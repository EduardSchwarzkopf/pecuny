# base_transaction_service.py
import asyncio
from datetime import datetime
from typing import List, Optional, Type

from app import models, schemas
from app.logger import get_logger
from app.repository import Repository
from app.services.accounts import AccountService
from app.services.base import BaseService
from app.utils.classes import RoundedDecimal
from app.utils.exceptions import AccessDeniedError
from app.utils.log_messages import ACCOUNT_USER_ID_MISMATCH

logger = get_logger(__name__)


class BaseTransactionService(BaseService):
    def __init__(
        self,
        service_model: Type[models.Transaction],
        repository: Optional[Repository] = None,
    ):
        self.service_model = service_model

        super().__init__(repository)

    async def get_transaction_list(
        self,
        user: models.User,
        account_id: int,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[models.Transaction]:
        logger.info(
            "Starting transaction list retrieval for user %s and account %s",
            user.id,
            account_id,
        )
        account = await self.repository.get(models.Account, account_id)

        if account is None or account.user_id != user.id:
            return []

        if date_start and date_end:
            return await self.repository.get_transactions_from_period(
                account_id, date_start, date_end
            )
        else:
            return await self.repository.filter_by(
                self.service_model,
                self.service_model.account_id,
                account.id,
            )

    async def get_transaction(
        self, user: models.User, transaction_id: int
    ) -> Optional[models.Transaction]:
        logger.info(
            "Retrieving transaction with ID %s for user %s", transaction_id, user.id
        )
        transaction = await self.repository.get(self.service_model, transaction_id)

        if transaction is None:
            logger.warning("Transaction with ID %s not found.", transaction_id)
            return None

        account = await self.repository.get(models.Account, transaction.account_id)

        if account is None:
            return None

        if account.user_id == user.id:
            logger.info("User ID verified. Returning transaction.")
            return transaction

        logger.warning(ACCOUNT_USER_ID_MISMATCH)
        return None

    async def delete_transaction(
        self, current_user: models.User, transaction_id: int
    ) -> Optional[bool]:
        logger.info(
            "Deleting transaction with ID %s for user %s",
            transaction_id,
            current_user.id,
        )

        transaction = await self.repository.get(
            self.service_model,
            transaction_id,
            load_relationships_list=[self.service_model.offset_transaction],
        )

        if transaction is None:
            logger.warning("Transaction with ID %s not found.", transaction_id)
            return None

        account = await self.repository.get(models.Account, transaction.account_id)

        if account is None or current_user.id != account.user_id:
            return None

        amount = transaction.information.amount

        if transaction.offset_transaction:
            logger.info("Handling offset transaction for delete.")
            offset_transaction = transaction.offset_transaction
            offset_account = await self.repository.get(
                models.Account, offset_transaction.account_id
            )

            if offset_account is None:
                return None

            offset_account.balance += amount
            await self.repository.delete(transaction.offset_transaction)

        account.balance -= amount
        await self.repository.delete(transaction)

        return True

    async def create_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        logger.info("Creating new transaction for user %s", user.id)
        account = await self.repository.get(models.Account, transaction_data.account_id)

        if account is None or not AccountService.has_user_access_to_account(
            user, account
        ):
            return None

        db_transaction_information = models.TransactionInformation()
        db_transaction_information.add_attributes_from_dict(
            transaction_data.model_dump()
        )

        transaction = self.service_model(
            information=db_transaction_information,
            account_id=account.id,
            scheduled_transaction_id=transaction_data.scheduled_transaction_id,
        )

        if transaction_data.offset_account_id:
            logger.info("Handling offset account for transaction.")
            offset_transaction = await self._handle_offset_transaction(
                user, transaction_data
            )

            if offset_transaction is None:
                logger.warning(
                    "User[id: %s] not allowed to access offset_account[id: %s]",
                    user.id,
                    transaction_data.offset_account_id,
                )
                raise AccessDeniedError(
                    (
                        f"User[id: {user.id}] not allowed to access "
                        f"offset_account[id: {transaction_data.offset_account_id}]"
                    )
                )

            transaction.offset_transaction = offset_transaction
            offset_transaction.offset_transaction = transaction
            await self.repository.save(offset_transaction)

        account.balance += db_transaction_information.amount

        await self.repository.save([account, transaction, db_transaction_information])

        return transaction

    async def _handle_offset_transaction(
        self,
        user: models.User,
        transaction_data: schemas.TransactionData,
    ) -> Optional[models.Transaction]:
        logger.info("Handling offset transaction for user %s", user.id)
        offset_account_id = transaction_data.offset_account_id
        if offset_account_id is None:
            return None

        offset_account = await self.repository.get(models.Account, offset_account_id)

        if offset_account is None or user.id != offset_account.user_id:
            logger.warning("User ID does not match the offset account's User ID.")
            return None

        transaction_data.amount = RoundedDecimal(transaction_data.amount * -1)
        offset_account.balance += transaction_data.amount

        db_offset_transaction_information = models.TransactionInformation()
        db_offset_transaction_information.add_attributes_from_dict(
            transaction_data.model_dump()
        )

        offset_transaction = self.service_model(
            information=db_offset_transaction_information,
            account_id=offset_account_id,
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
        logger.info(
            "Updating transaction with ID %s for user %s",
            transaction_id,
            current_user.id,
        )

        transaction = await self.repository.get(
            self.service_model,
            transaction_id,
            load_relationships_list=[self.service_model.account],
        )

        if transaction is None:
            return None

        account = transaction.account
        if current_user.id != account.user_id:
            logger.warning(ACCOUNT_USER_ID_MISMATCH)
            return None

        amount_updated = (
            round(transaction_information.amount, 2) - transaction.information.amount
        )

        if transaction.offset_transactions_id:
            logger.info("Handling offset transaction for update.")
            offset_transaction = await self.repository.get(
                self.service_model,
                transaction.offset_transactions_id,
                load_relationships_list=[self.service_model.account],
            )

            if offset_transaction is None:
                return None

            offset_account = offset_transaction.account
            if offset_account is None or offset_account.user_id != current_user.id:
                return None

            offset_account.balance -= amount_updated
            offset_transaction.information.amount = transaction_information.amount * -1

        account_values = {"balance": account.balance + amount_updated}
        await self.repository.update(models.Account, account.id, **account_values)

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
