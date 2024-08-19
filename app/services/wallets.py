from typing import Optional

from app import models, schemas
from app.config import settings
from app.logger import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class WalletService(BaseService):

    async def get_wallets(self, current_user: models.User) -> list[models.Wallet]:
        """
        Retrieves a list of wallets.

        Args:
            current_user: The current active user.

        Returns:
            list[Wallet]: A list of wallet objects.
        """

        return (
            await self.repository.filter_by(
                models.Wallet, models.Wallet.user_id, current_user.id
            )
            or []
        )

    async def get_wallet(
        self, current_user: models.User, wallet_id: int
    ) -> Optional[models.Wallet]:
        """
        Retrieves an wallet by ID.

        Args:
            current_user: The current active user.
            wallet_id: The ID of the wallet to retrieve.

        Returns:
            Wallet: The retrieved wallet object.
        """

        logger.info("Getting wallet %s for user: %s", wallet_id, current_user.id)
        wallet = await self.repository.get(models.Wallet, wallet_id)

        if wallet is None:
            return None

        if self.has_user_access_to_wallet(current_user, wallet):
            logger.info("Found wallet %s for user: %s", wallet_id, current_user.id)
            return wallet

        return None

    async def create_wallet(
        self, user: models.User, wallet: schemas.Wallet
    ) -> models.Wallet:
        """
        Creates a new wallet.

        Args:
            user: The user object.
            wallet: The wallet data.

        Returns:
            Wallet: The created wallet object.
        """

        logger.info("Creating new wallet for user: %s", user.id)
        db_wallet = models.Wallet(user=user, **wallet.model_dump())
        await self.repository.save(db_wallet)
        logger.info("Wallet created for user: %s", user.id)
        return db_wallet

    async def update_wallet(
        self, current_user: models.User, wallet_id, wallet: schemas.WalletData
    ) -> Optional[models.Wallet]:
        """
        Updates an wallet.

        Args:
            current_user: The current active user.
            wallet_id: The ID of the wallet to update.
            wallet: The updated wallet data.

        Returns:
            Wallet: The updated wallet information.
        """

        logger.info("Updating wallet %s for user: %s", wallet_id, current_user.id)
        db_wallet = await self.repository.get(models.Wallet, wallet_id)

        if db_wallet is None:
            return None

        if db_wallet.user_id == current_user.id:
            await self.repository.update(
                models.Wallet, db_wallet.id, **wallet.model_dump()
            )
            logger.info("Wallet %s updated for user:  %s", wallet, current_user.id)
            return db_wallet
        logger.warning(
            "Wallet %s not found or does not belong to user: %s",
            wallet,
            current_user.id,
        )
        return None

    async def delete_wallet(
        self, current_user: models.User, wallet_id: int
    ) -> Optional[bool]:
        """
        Deletes an wallet.

        Args:
            current_user: The current active user.
            wallet_id: The ID of the wallet to delete.

        Returns:
            bool: True if the wallet is successfully deleted, False otherwise.
        """

        logger.info("Deleting wallet %s for user: %s", wallet_id, current_user.id)
        wallet = await self.repository.get(models.Wallet, wallet_id)
        if wallet and wallet.user_id == current_user.id:
            await self.repository.delete(wallet)
            logger.info("Wallet %s deleted for user: %s", wallet_id, current_user.id)
            return True
        logger.warning(
            "Wallet %s not found or does not belong to user: %s",
            wallet_id,
            current_user.id,
        )
        return None

    async def check_max_wallets(self, user: models.User) -> bool:
        """
        Checks if the maximum number of wallets has been reached for a user.

        Args:
            user: The user object.

        Returns:
            bool: True if the maximum number of wallets has been reached, False otherwise.
        """

        logger.info("Checking if maximum wallets reached for user: %s", user.id)
        wallet_list = await self.get_wallets(user)

        if wallet_list is None:
            return True

        result = len(wallet_list) >= settings.max_allowed_wallets
        if result:
            logger.warning(
                "User %s has reached the maximum allowed wallets limit.", user.id
            )
        return result

    @staticmethod
    def calculate_total_balance(wallet_list: list[models.Wallet]) -> float:
        """
        Calculates the total balance of a list of wallets.

        Args:
            wallet_list: A list of wallet objects.

        Returns:
            float: The total balance of the wallets.
        """

        return sum(wallet.balance for wallet in wallet_list)

    @staticmethod
    def has_user_access_to_wallet(user: models.User, wallet: models.Wallet) -> bool:
        """
        Check if the user has access to the wallet.

        Args:
            user: The user object.
            wallet: The wallet object.

        Returns:
            bool: True if the user has access to the wallet, False otherwise.
        """
        return user.id == wallet.user_id