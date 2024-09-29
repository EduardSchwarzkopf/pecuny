from typing import TypeVar

from fastapi import HTTPException

from app.models import Base

ModelT = TypeVar("ModelT", bound=Base)
HTTPExceptionT = TypeVar("HTTPExceptionT", bound=HTTPException)
