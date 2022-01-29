from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

from pydantic.types import constr


def username_alphanumeric(username: str):
    assert username.isalnum(), "must be alphanumeric"
    return username


def _validate_username():
    return validator("username", allow_reuse=True)(username_alphanumeric)


class Base(BaseModel):
    class Config:
        orm_mode = True


class UserBase(Base):
    username: constr(to_lower=True)
    email: EmailStr

    _validate_username = _validate_username()


class UserCreate(UserBase):
    password: str


class UserData(UserBase):
    id: int


class UserUpdate(Base):
    username: Optional[str] = ""
    email: Optional[EmailStr] = ""
    password: Optional[str] = None

    _validate_username = _validate_username()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str]
