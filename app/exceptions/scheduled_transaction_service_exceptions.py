from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class ScheduledTransactionNotFoundException(EntityNotFoundException):
    def __init__(self, scheduled_transaction_id: IdField):
        self.scheduled_transaction_id = scheduled_transaction_id
        super().__init__(models.TransactionScheduled, scheduled_transaction_id)
