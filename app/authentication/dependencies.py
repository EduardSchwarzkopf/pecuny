from functools import lru_cache
from typing import AsyncGenerator

from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app import models
from app.authentication.management import UserManager
from app.authentication.strategies import JWTAccessRefreshStrategy
from app.config import settings
from app.database import SessionLocal


async def get_user_manager() -> AsyncGenerator[UserManager, None]:
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
    async with SessionLocal() as session:
        user_db = SQLAlchemyUserDatabase(session, models.User, models.OAuthAccount)
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
