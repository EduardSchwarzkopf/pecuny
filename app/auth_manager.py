import uuid
from typing import Optional

from fastapi import Depends, Request


from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from app.config import settings

from app.database import get_user_db
from app.models import User
from app.services import email

SECRET = settings.secret_key
TOKEN_EXPIRE = settings.access_token_expire_minutes * 60
SECURE_COOKIE = settings.enviroment != "dev"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        if user.is_verified:
            return

        await self.request_verify(user, request)
        await email.send_register(user)

        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email.send_forgot_password(user, token)
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email.send_verification(user, token)
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_max_age=TOKEN_EXPIRE, cookie_secure=SECURE_COOKIE
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=TOKEN_EXPIRE)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True, verified=True)
optional_current_active_verified_user = fastapi_users.current_user(
    active=True, verified=True, optional=True
)
