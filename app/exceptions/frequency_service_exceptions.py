from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class FrequencyNotFoundException(EntityNotFoundException):
    def __init__(self, user: models.User, frequency_id: IdField):
        self.transaction_id = frequency_id
        super().__init__(user, models.Frequency, frequency_id)
