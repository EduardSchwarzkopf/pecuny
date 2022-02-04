import re
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List

from pydantic.types import constr


def username_validator(username: str):
    assert re.match(r"^\w+$", username), "must be alphanumeric"
    return username


def _validate_username():
    return validator("username", allow_reuse=True)(username_validator)


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


class AccountUpdate(Base):
    label: Optional[constr(strip_whitespace=True, min_length=1, max_length=36)]
    description: Optional[str]
    balance: Optional[float]


class TransactionSubcategory(Base):
    id: int
    label: str
    is_income: bool
    parent_category_id: int


class TransactionInformation(Base):
    amount: float
    reference: str
    date: datetime
    subcategory_id: int


class TransactionInformationCreate(TransactionInformation):
    account_id: int


class TransactionInformationData(TransactionInformation):
    id: int
    subcategory: TransactionSubcategory


class Transaction(Base):
    account_id: int
    information: TransactionInformationData


class Account(Base):
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    description: Optional[str]
    balance: Optional[float]


class AccountData(Account):
    id: int
    transactions: List[Transaction]


class TransactionQuery(BaseModel):
    account_id: int
    date_start: datetime
    date_end: datetime
