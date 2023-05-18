import uuid

from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from fastapi_users import schemas

from pydantic.types import constr


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: Dict[str, Any]


class UserRead(schemas.BaseUser[uuid.UUID]):
    displayname: str


class UserCreate(schemas.BaseUserCreate):
    displayname: str


class UserUpdate(schemas.BaseUserUpdate):
    displayname: str


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


class TransactionInformationBase(Base):
    amount: float
    reference: str
    category_id: int


class TransactionInformation(TransactionInformationBase):
    date: datetime


class MinimalResponse(Base):
    id: int
    label: str


class SectionData(MinimalResponse):
    pass


class FrequencyData(MinimalResponse):
    pass


class CategoryData(Base):
    id: int
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    section: SectionData


class TransactionInformationCreate(TransactionInformation):
    account_id: int
    offset_account_id: Optional[int]


class TransactionInformtionUpdate(TransactionInformationCreate):
    pass


class ScheduledTransactionInformationCreate(TransactionInformationBase):
    date_start: datetime
    frequency_id: int
    date_end: datetime
    account_id: int
    offset_account_id: Optional[int]


class TransactionInformationData(TransactionInformation):
    category: CategoryData


class TransactionBase(Base):
    id: int
    account_id: int
    information: TransactionInformationData


class Transaction(TransactionBase):
    offset_transactions_id: Optional[int]


class ScheduledTransactionData(TransactionBase):
    date_start: datetime
    frequency: FrequencyData
    date_end: datetime
    account_id: int
    offset_account_id: Optional[int]


class Account(Base):
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    description: str
    balance: float


class AccountData(Account):
    id: int
