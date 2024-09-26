from typing import Optional

from app import models, schemas
from app.config import settings
from app.exceptions.wallet_service_exceptions import (
    WalletAccessDeniedException,
    WalletLimitReachedException,
)
from app.repository import Repository
from app.services.base import BaseService


class WalletService(BaseService):

    def __init__(self, repository: Optional[Repository] = None):
        super().__init__(repository)

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

    async def __get_wallet_by_id(self, wallet_id: int):
        return await self.repository.get(models.Wallet, wallet_id)

    async def get_wallet(self, user: models.User, wallet_id: int) -> models.Wallet:

        wallet = await self.__get_wallet_by_id(wallet_id)

        if not self.has_user_access_to_wallet(user, wallet):
            raise WalletAccessDeniedException(user, wallet)

        return wallet

    async def create_wallet(
        self, user: models.User, wallet: schemas.Wallet
    ) -> models.Wallet:

        if await self.has_reached_wallet_limit(user):
            raise WalletLimitReachedException(user)

        db_wallet = models.Wallet(user=user, **wallet.model_dump())
        await self.repository.save(db_wallet)
        return db_wallet

    async def update_wallet(
        self, user: models.User, wallet_id, wallet: schemas.WalletData
    ) -> models.Wallet:

        db_wallet = await self.repository.get(models.Wallet, wallet_id)

        if db_wallet is None:
            raise WalletNotFoundException(user, wallet_id)

        if self.has_user_access_to_wallet(user, db_wallet):
            await self.repository.update(
                models.Wallet, db_wallet.id, **wallet.model_dump()
            )
            return db_wallet

        raise WalletAccessDeniedException(user, wallet)

    async def delete_wallet(self, user: models.User, wallet_id: int) -> True:

        wallet = await self.repository.get(models.Wallet, wallet_id)

        if wallet is None:
            raise WalletNotFoundException(user, wallet_id)

        if self.has_user_access_to_wallet(user, wallet):
            await self.repository.delete(wallet)
            return True

        raise WalletAccessDeniedException(user, wallet)

    async def check_max_wallets(self, user: models.User) -> bool:
        """
        Checks if the maximum number of wallets has been reached for a user.

        Args:
            user: The user object.

        Returns:
            bool: True if the maximum number of wallets has been reached, False otherwise.
        """

        wallet_list = await self.get_wallets(user)

        if wallet_list is None:
            return True

        return len(wallet_list) >= settings.max_allowed_wallets

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

    async def validate_access_to_wallet(
        self, user: models.User, wallet_id: int
    ) -> None:
        """
        Validates if the user has access to the wallet.

        Args:
            user: The user object.
            wallet_id: The wallet ID.

        Raises:
            WalletAccessDeniedException: If the user does not have access to the wallet.
        """

        wallet = await self.__get_wallet_by_id(wallet_id)

        if not self.has_user_access_to_wallet(user, wallet):
            raise WalletAccessDeniedException(user, wallet)

        return

    def has_user_access_to_wallet(
        self, user: models.User, wallet: models.Wallet
    ) -> bool:
        """
        Check if the user has access to the wallet.

        Args:
            user: The user object.
            wallet: The wallet object.

        Returns:
            bool: True if the user has access to the wallet, False otherwise.
        """

        return user.id == wallet.user_id
