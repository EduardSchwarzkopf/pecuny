from app import models
from app.exceptions.base_service_exception import (
    BaseServiceException,
    EntityAccessDeniedException,
)


class WalletAccessDeniedException(EntityAccessDeniedException):
    def __init__(self, user: models.User, wallet: models.Wallet):
        super().__init__(user, wallet)


class WalletLimitReachedException(BaseServiceException):
    def __init__(self, user: models.User):
        super().__init__(f"User with {user.id} has reached the limit of wallets.")
