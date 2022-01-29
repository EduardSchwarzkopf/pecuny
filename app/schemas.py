from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

from pydantic.types import constr


class Base(BaseModel):
    class Config:
        orm_mode = True


class UserBase(Base):
    username: constr(to_lower=True)
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserData(UserBase):
    id: int


class UserUpdate(Base):
    username: Optional[str] = ""
    email: Optional[EmailStr] = ""
    password: Optional[str] = ""


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str]
