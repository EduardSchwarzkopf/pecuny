from abc import ABC, abstractmethod
from typing import Type

from pydantic_core import core_schema


class BaseField(ABC):

    @abstractmethod
    def _validate(self) -> Type:
        pass

    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        return core_schema.no_info_after_validator_function(
            cls._validate, core_schema.decimal_schema()
        )


class IdField(BaseField, int):
    @classmethod
    def _validate(cls, value: int):
        if isinstance(value, int) and value > 0:
            return value

        raise ValueError("Invalid Id provided")

    @classmethod
    def _serialize(cls, value):
        return value
