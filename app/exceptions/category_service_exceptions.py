from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class CategoryNotFoundException(EntityNotFoundException):
    def __init__(self, user: models.User, category_id: IdField):
        self.transaction_id = category_id
        super().__init__(user, models.TransactionCategory, category_id)
