from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class TransactionNotFoundException(EntityNotFoundException):
    def __init__(self, user: models.User, transaction_id: IdField):
        self.transaction_id = transaction_id
        super().__init__(user, models.Transaction, transaction_id)
