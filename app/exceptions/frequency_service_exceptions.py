from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class FrequencyNotFoundException(EntityNotFoundException):
    def __init__(self, frequency_id: IdField):
        self.transaction_id = frequency_id
        super().__init__(models.Frequency, frequency_id)
