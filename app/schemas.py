from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

from pydantic.types import conint


class Base(BaseModel):
    class Config:
        orm_mode = True


class UserBase(Base):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserData(UserBase):
    id: int


class UserLogin(UserCreate):
    pass
