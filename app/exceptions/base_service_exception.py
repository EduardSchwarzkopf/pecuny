from abc import ABC

from app import models
from app.utils.fields import IdField


class BaseServiceException(ABC, Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundException(BaseServiceException):
    def __init__(self, model: models.Base, entity_id: IdField):
        self.entity_model_class_name = model.__name__
        self.entity_id = entity_id

        super().__init__(
            f"Could not find {self.entity_model_class_name} with ID {self.entity_id}."
        )


class EntityAccessDeniedException(BaseServiceException):
    def __init__(self, user: models.User, entity: models.BaseModel):
        self.entity = entity
        self.entity_class_name = entity.__class__.__name__
        self.user = user

        super().__init__(
            f"Access to {self.entity_class_name} with ID {self.entity.id} is denied "
            f"to user with ID {self.user.id}."
        )
