from dataclasses import dataclass

from fastapi import Request


@dataclass
class CreateUserData:
    email: str
    password: str
    displayname: str = ""
    is_verified: bool = False
    is_superuser: bool = False
    request: Request = None
