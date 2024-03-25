import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, Request, Response, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.jwt import SecretType, generate_jwt

from app.config import settings
from app.database import get_user_db
from app.models import User
from app.services import email

VERIFICATION_SECRET = settings.verify_token_secret_key
ACCESS_TOKEN_EXPIRE = settings.access_token_expire_minutes * 60
SECURE_COOKIE = settings.enviroment != "dev"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = VERIFICATION_SECRET
    verification_token_secret = VERIFICATION_SECRET

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


class CustomJWTStrategy(JWTStrategy[models.UP, models.ID]):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        access_token_secret: SecretType,
        refresh_token_secret: SecretType,
        lifetime_seconds: Optional[int],
        refresh_lifetime_seconds: Optional[int],
        token_audience: Optional[List[str]] = None,
        algorithm: str = "HS256",
        public_key: Optional[SecretType] = None,
    ):
        if token_audience is None:
            token_audience = settings.token_audience

        super().__init__(
            secret=access_token_secret,
            lifetime_seconds=lifetime_seconds,
            token_audience=token_audience,
            algorithm=algorithm,
            public_key=public_key,
        )

        self.refresh_lifetime_seconds = refresh_lifetime_seconds
        self.refresh_token_secret = refresh_token_secret

    async def write_refresh_token(self, user: User) -> str:
        """
        Generates a JWT refresh token for the given user.

        Args:
            user: The user object for whom the token is generated.

        Returns:
            str: The generated JWT refresh token.

        Raises:
            Any errors raised by the JWT generation process.
        """

        data = {"sub": str(user.id), "aud": self.token_audience}
        return generate_jwt(
            data,
            self.refresh_token_secret,
            self.refresh_lifetime_seconds,
            algorithm=self.algorithm,
        )

    async def write_token(self, user: models.UP) -> str:
        """
        Generates a JWT token for the given user.

        Args:
            user: The user object for whom the token is generated.

        Returns:
            str: The generated JWT token.

        Raises:
            Any errors raised by the JWT generation process.
        """

        data = {"sub": str(user.id), "aud": self.token_audience}
        return generate_jwt(
            data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm
        )


class CustomAuthenticationBackend(AuthenticationBackend):

    async def login(self, strategy: CustomJWTStrategy, user: User) -> Response:
        """
        Logs in a user by generating access and refresh tokens using the provided JWT strategy.

        Args:
            strategy: The custom JWT strategy used for token generation.
            user: The user object logging in.

        Returns:
            Response: The HTTP response containing the tokens as cookies.
        """

        access_token = await strategy.write_token(user)
        refresh_token = await strategy.write_refresh_token(user)

        response = Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

        response.set_cookie(
            settings.access_token_name,
            access_token,
            max_age=strategy.lifetime_seconds,
            secure=SECURE_COOKIE,
        )

        response.set_cookie(
            settings.refresh_token_name,
            refresh_token,
            max_age=strategy.refresh_lifetime_seconds,
            secure=SECURE_COOKIE,
        )

        return response


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """
    Asynchronously yields a UserManager for the provided user.

    Args:
        user_db: The user object.

    Yields:
        UserManager: A manager for the user.

    Raises:
        UserInactive: If the user is inactive.
        UserAlreadyVerified: If the user is already verified.
    """
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="access_token",
    cookie_max_age=ACCESS_TOKEN_EXPIRE,
    cookie_secure=SECURE_COOKIE,
)


def get_strategy() -> CustomJWTStrategy:
    """
    Returns a custom JWT strategy with specified secret and token lifetimes.

    Returns:
        CustomJWTStrategy: The custom JWT strategy object.
    """

    return CustomJWTStrategy(
        access_token_secret=settings.access_token_secret_key,
        lifetime_seconds=ACCESS_TOKEN_EXPIRE,
        refresh_lifetime_seconds=settings.refresh_token_expire_minutes * 60,
        refresh_token_secret=settings.refresh_token_secret_key,
    )


auth_backend = CustomAuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True, verified=True)
optional_current_active_verified_user = fastapi_users.current_user(
    active=True, verified=True, optional=True
)
