from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Union

from pydantic_core import core_schema

from app.date_manager import string_to_datetime


class BaseField(ABC):

    @classmethod
    @abstractmethod
    def _validate(cls, value: Any) -> Any:
        """
        Define an abstract method to validate a value and
        return the validated type.
        """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        return core_schema.no_info_after_validator_function(
            cls._validate, core_schema.any_schema()
        )

    @classmethod
    def _serialize(cls, value):
        return value


class IdField(BaseField, int):
    @classmethod
    def _validate(cls, value: Union[int, str, None]) -> Optional[int]:
        if value is None or value == 0:
            return None

        if isinstance(value, str):
            if value.strip() == "":
                return None
            try:
                value = int(value)
            except ValueError as e:
                raise ValueError("Invalid Id provided") from e

        if isinstance(value, int) and value > 0:
            return value

        raise ValueError("Invalid Id provided")


class DateField(BaseField, datetime):
    @classmethod
    def _validate(cls, value: Union[str, datetime]) -> datetime:
        """
        Validates and parses a date string into a datetime object.

        Args:
            cls: The class.
            value: The date string to parse.

        Returns:192gg
            datetime: The parsed datetime object.

        Raises:
            ValueError: If the date format is not recognized.
        """

        if isinstance(value, datetime):
            return value

        try:
            return string_to_datetime(value)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid date provided") from e
