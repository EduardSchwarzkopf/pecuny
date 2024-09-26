from app import models
from app.exceptions.base_service_exception import (
    BaseServiceException,
    EntityAccessDeniedException,
)


class WalletAccessDeniedException(EntityAccessDeniedException):
    def __init__(self, user: models.User, wallet: models.Wallet):
        self.wallet = wallet
        self.user = user
        super().__init__(self.user, self.wallet)
