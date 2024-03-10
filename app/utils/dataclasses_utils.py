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
    request: Optional[Request] = None
