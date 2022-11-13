import uuid

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from fastapi_users import schemas

from pydantic.types import constr


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class Base(BaseModel):
    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


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
    offset_account_id: Optional[int]


class TransactionInformtionUpdate(TransactionInformationCreate):
    pass


class TransactionInformationData(TransactionInformation):
    subcategory: TransactionSubcategory


class Transaction(Base):
    id: int
    account_id: int
    information: TransactionInformationData
    offset_transactions_id: Optional[int]


class Account(Base):
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    description: Optional[str]
    balance: Optional[float]


class AccountData(Account):
    id: int


class TransactionQuery(BaseModel):
    account_id: int
    date_start: datetime
    date_end: datetime
