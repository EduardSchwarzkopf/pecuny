from app import models, schemas
from app.config import settings
from app.exceptions.wallet_service_exceptions import (
    WalletAccessDeniedException,
    WalletLimitReachedException,
)
from app.services.base import BaseService


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

    async def __get_wallet_by_id(self, wallet_id: int):
        """
        Retrieves a wallet by its ID using the repository.

        Args:
            wallet_id: The ID of the wallet to retrieve.

        Returns:
            models.Wallet: The wallet object associated with the provided ID.
        """

        return await self.repository.get(models.Wallet, wallet_id)

    async def get_wallet(self, user: models.User, wallet_id: int) -> models.Wallet:
        """
        Retrieves a wallet for a specific user based on the wallet ID.

        Args:
            user: The user for whom the wallet is being retrieved.
            wallet_id: The ID of the wallet to retrieve.

        Returns:
            models.Wallet: The wallet associated with the provided ID.

        Raises:
            WalletAccessDeniedException: If the user does not have access to the wallet.
        """

        wallet = await self.__get_wallet_by_id(wallet_id)

        if not self.has_user_access_to_wallet(user, wallet):
            raise WalletAccessDeniedException(user, wallet)

        return wallet

    async def create_wallet(
        self, user: models.User, wallet: schemas.Wallet
    ) -> models.Wallet:
        """
        Creates a new wallet for a user based on the provided wallet data.

        Args:
            user: The user for whom the wallet is being created.
            wallet: The wallet data to create the new wallet.

        Returns:
            models.Wallet: The newly created wallet object.

        Raises:
            WalletLimitReachedException: If the user has reached the wallet limit.
        """

        if await self.has_reached_wallet_limit(user):
            raise WalletLimitReachedException(user)

        db_wallet = models.Wallet(user=user, **wallet.model_dump())
        await self.repository.save(db_wallet)
        return db_wallet

    async def update_wallet(
        self, user: models.User, wallet_id, wallet_data: schemas.WalletData
    ) -> models.Wallet:
        """
        Updates an existing wallet for a user with the provided wallet data.

        Args:
            user: The user for whom the wallet is being updated.
            wallet_id: The ID of the wallet to update.
            wallet_data: The updated wallet data.

        Returns:
            models.Wallet: The updated wallet object.
        """

        db_wallet = await self.get_wallet(user, wallet_id)

        await self.repository.update(
            models.Wallet, db_wallet.id, **wallet_data.model_dump()
        )

        return db_wallet

    async def delete_wallet(self, user: models.User, wallet_id: int) -> True:
        """
        Deletes a wallet for a specific user based on the wallet ID.

        Args:
            user: The user for whom the wallet is being deleted.
            wallet_id: The ID of the wallet to delete.

        Returns:
            True: If the wallet is successfully deleted.
        """

        wallet = await self.get_wallet(user, wallet_id)
        await self.repository.delete(wallet)
        return True

    async def has_reached_wallet_limit(self, user: models.User) -> bool:
        """
        Checks if the maximum number of wallets has been reached for a user.

        Args:
            user: The user object.

        Returns:
            bool: True if the maximum number of wallets has been reached, False otherwise.
        """

        wallet_list = await self.get_wallets(user)

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
