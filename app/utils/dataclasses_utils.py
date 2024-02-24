from dataclasses import dataclass

from fastapi import Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CreateUserData:
    email: str
    password: str
    displayname: str = ""
    is_verified: bool = False
    is_superuser: bool = False
    request: Request = None


@dataclass
class ClientSessionWrapper:
    client: AsyncClient = None
    authorized_client: AsyncClient = None
    session: AsyncSession = None
