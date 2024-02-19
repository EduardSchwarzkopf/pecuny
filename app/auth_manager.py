import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.jwt import generate_jwt
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

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        if user.is_verified or (request and request.url.hostname == "test"):
            return

        await self.request_verify(user, request)
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        await email.send_forgot_password(user, token)
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email.send_welcome(user, token)
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def request_verify(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        if not user.is_active:
            raise exceptions.UserInactive()
        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        await self.on_after_request_verify(user, self.get_token(user), request)

    def get_token(self, user: User) -> str:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "aud": self.verification_token_audience,
        }
        return generate_jwt(
            token_data,
            self.verification_token_secret,
            self.verification_token_lifetime_seconds,
        )

    async def request_new_token(self, user: User) -> None:
        if not user.is_active:
            raise exceptions.UserInactive()
        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        await email.send_new_token(user, self.get_token(user))


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
