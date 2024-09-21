from abc import ABC

from kombu import entity

from app import models
from app.utils.fields import IdField


class BaseServiceException(ABC, Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def details(self):
        return f"{type(self).__name__} at line {self.__traceback__.tb_lineno} of {__file__}: {self}"


class EntityNotFoundException(BaseServiceException):
    def __init__(self, model: models.Base, entity_id: IdField):
        self.model_entity_name = model.__name__
        self.entity_id = entity_id
        super().__init__(f"{self.model_entity_name} with ID {self.entity_id} not found")


class EntityAccessDeniedException(BaseServiceException):
    def __init__(self, user: models.User, entity: models.BaseModel):
        self.entity = entity
        self.entity_id = entity.id
        self.entity_name = entity.__class__.__name__
        self.user = user
        super().__init__(
            f"User with ID {user.id} is not allowed to access {self.entity_name} with ID {self.entity_id}"
        )
