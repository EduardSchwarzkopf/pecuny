from typing import TypeVar

from app.models import Base

ModelT = TypeVar("ModelT", bound=Base)
