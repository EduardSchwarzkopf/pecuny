from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class ScheduledTransactionNotFoundException(EntityNotFoundException):
    def __init__(self, user: models.User, scheduled_transaction_id: IdField):
        self.scheduled_transaction_id = scheduled_transaction_id
        super().__init__(user, models.TransactionScheduled, scheduled_transaction_id)
