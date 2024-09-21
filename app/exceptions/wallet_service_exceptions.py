from app import models
from app.exceptions.base_service_exception import (
    EntityAccessDeniedException,
    EntityNotFoundException,
)
from app.utils.fields import IdField


class WalletNotFoundException(EntityNotFoundException):
    def __init__(self, wallet_id: IdField):
        self.wallet_id = wallet_id
        super().__init__(models.Wallet, wallet_id)


class WalletAccessDeniedException(EntityAccessDeniedException):
    def __init__(self, user: models.User, wallet: models.Wallet):
        self.wallet = wallet
        self.user = user
        super().__init__(self.user, self.wallet)
