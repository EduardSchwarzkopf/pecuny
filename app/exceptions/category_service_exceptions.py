from app import models
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.fields import IdField


class CategoryNotFoundException(EntityNotFoundException):
    def __init__(self, category_id: IdField):
        super().__init__(models.TransactionCategory, category_id)
