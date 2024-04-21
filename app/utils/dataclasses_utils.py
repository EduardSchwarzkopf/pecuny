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
class FailedImportedTransaction:
    section: str
    category: str
    amount: str
    date: str
    reference: str
    reason: str = ""
    offset_account_id: Optional[int] = None
