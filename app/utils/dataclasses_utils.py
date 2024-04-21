from dataclasses import dataclass
from typing import Optional

from fastapi import Request


@dataclass
class CreateUserData:
    email: str
    password: str
    displayname: Optional[str] = ""
    is_verified: Optional[bool] = False
    is_superuser: Optional[bool] = False
    is_active: Optional[bool] = True
    request: Optional[Request] = None


@dataclass
class ImportedTransaction:
    date: str
    reference: str
    amount: float
    section: str
    category: str
    offset_account_id: Optional[int] = None


@dataclass
class FailedImportedTransaction(ImportedTransaction):
    reason: str = ""
