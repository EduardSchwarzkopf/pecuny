import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin, exceptions
from fastapi_users.jwt import generate_jwt

from app.config import settings
from app.models import User
from app.services import email

VERIFICATION_SECRET = settings.verify_token_secret_key


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = VERIFICATION_SECRET
    verification_token_secret = VERIFICATION_SECRET

    async def on_after_update(
        self,
        user: User,
        update_dict: Dict[str, Any],
        request: Optional[Request] = None,
    ) -> None:

        if "email" in update_dict:
            print("send verification email to ", update_dict["email"])

        pass

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
        print(f"User {user.id} has forgot their password.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email.send_welcome(user, token)
        print(f"Verification requested for user {user.id}.")

    async def request_verify(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        if not user.is_active:
            raise exceptions.UserInactive()
        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        await self.on_after_request_verify(user, self.get_token(user), request)

    def get_token(self, user: User) -> str:
        """Generate a token for the specified user.

        Args:
            user: The user object.

        Returns:
            str: The generated token.

        Raises:
            None
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "aud": self.verification_token_audience,
        }
        return generate_jwt(
            token_data,
            self.verification_token_secret,
            self.verification_token_lifetime_seconds,
            settings.algorithm,
        )

    async def request_new_token(self, user: User) -> None:
        """Request a new token for the specified user.

        Args:
            user: The user object.

        Returns:
            None

        Raises:
            UserInactive: If the user is inactive.
            UserAlreadyVerified: If the user is already verified.
        """
        if not user.is_active:
            raise exceptions.UserInactive()
        if user.is_verified:
            raise exceptions.UserAlreadyVerified()

        await email.send_new_token(user, self.get_token(user))
