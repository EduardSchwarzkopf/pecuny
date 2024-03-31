from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase

from app.authentication.management import UserManager
from app.authentication.strategies import JWTAccessRefreshStrategy
from app.config import settings
from app.database import get_user_db
from app.services.users import UserService


@lru_cache
async def get_user_service() -> UserService:
    """
    Returns an instance of the UserService class.

    Returns:
        UserService: An instance of the UserService class.
    """

    return UserService()


@lru_cache
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


@lru_cache
def get_strategy() -> JWTAccessRefreshStrategy:
    """
    Returns a custom JWT strategy with specified secret and token lifetimes.

    Returns:
        CustomJWTStrategy: The custom JWT strategy object.
    """

    return JWTAccessRefreshStrategy(
        access_token_secret=settings.access_token_secret_key,
        lifetime_seconds=settings.access_token_expire_minutes,
        refresh_token_secret=settings.refresh_token_secret_key,
        refresh_lifetime_seconds=settings.refresh_token_expire_minutes,
    )
