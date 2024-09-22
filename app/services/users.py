from typing import Optional

from fastapi import Request
from fastapi_users import exceptions

from app import database, models, schemas
from app.authentication.management import UserManager
from app.database import db
from app.exceptions.user_service_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.repository import Repository
from app.schemas import EmailStr, UserCreate
from app.services.base import BaseService
from app.utils.dataclasses_utils import CreateUserData
from app.utils.displayname_generator import generate_displayname
from app.utils.enums import EmailVerificationStatus


class UserService(BaseService):
    """
    Provides user-related services.

    Methods:
    - delete_self: Deletes the current user.
    - update_user: Updates a user.
    - create_user: Creates a new user.
    - validate_new_user: Validates a new user.
    - verify_email: Verifies an email address.
    - forgot_password: Handles the forgot password process.
    - reset_password: Resets a user's password.
    """

    def __init__(self, repository: Optional[Repository] = None):
        """
        Initializes the UserService.

        Args:
            self: The UserService instance.

        Returns:
            None
        """

        super().__init__(repository)
        self.user_manager = self._get_user_manager()

    def _get_user_manager(self):
        """
        Gets the user manager.

        Args:
            self: The UserService instance.

        Returns:
            UserManager: The user manager instance.
        """

        user_db = database.SQLAlchemyUserDatabase(
            db.session, models.User, models.OAuthAccount
        )

        return UserManager(user_db)

    async def delete_self(self, current_user: models.User) -> bool:
        """
        Deletes the user.

        Args:
            current_user: The current user object.

        Returns:
            bool: True if the user is successfully deleted, False otherwise.
        """

        await self.repository.delete(current_user)

        return True

    async def update_user(
        self,
        user: models.User,
        user_data: schemas.UserUpdate,
        request: Optional[Request] = None,
    ) -> models.User:
        """
        Updates a user.

        Args:
            user: The user object.

        Returns:
            bool: User object.
        """

        return await self.user_manager.update(user_data, user, request=request)

    async def create_user(
        self,
        user_data: CreateUserData,
        request: Optional[Request] = None,
    ) -> Optional[models.User]:
        """
        Creates a new user.

        Args:
            user_data: The data for creating a new user.
            request: The request object.

        Returns:
            bool: True if the user is successfully created, False otherwise.

        Raises:
            None
        """

        if not user_data.displayname:
            user_data.displayname = generate_displayname()

        try:
            return await self.user_manager.create(
                UserCreate(
                    email=user_data.email,
                    displayname=user_data.displayname,
                    password=user_data.password,
                    is_superuser=user_data.is_superuser,
                    is_verified=user_data.is_verified,
                    is_active=user_data.is_active,
                ),
                request=request,
            )
        except exceptions.UserAlreadyExists:
            return None

    async def validate_new_user(self, email) -> None:
        """
        Validates a new user with the given email.

        Args:
            email: The email of the user.

        Returns:
            None

        Raises:
            UserAlreadyExistsException: If a user with the given email already exists.
        """

        try:
            existing_user = await self.user_manager.get_by_email(email)
        except exceptions.UserNotExists:
            existing_user = None

        if existing_user is not None:
            raise UserAlreadyExistsException(email)

    async def verify_email(self, token: str) -> EmailVerificationStatus:
        """
        Verifies an email with the given token.

        Args:
            token: The verification token.

        Returns:
            EmailVerificationStatus: The status of the email verification.

        Raises:
            None
        """

        try:
            await self.user_manager.verify(token)
            return EmailVerificationStatus.VERIFIED
        except exceptions.InvalidVerifyToken:
            return EmailVerificationStatus.INVALID_TOKEN
        except exceptions.UserAlreadyVerified:
            return EmailVerificationStatus.ALREADY_VERIFIED

    async def forgot_password(self, email: EmailStr) -> None:
        """
        Processes the forgot password request for the given email.

        Args:
            email: The email address of the user.

        Returns:
            None

        Raises:
            UserNotFoundException: If no user is found with the given email.
        """

        try:
            existing_user = await self.user_manager.get_by_email(email)
            if existing_user is None:
                raise UserNotFoundException(email)
            await self.user_manager.forgot_password(existing_user)
        except exceptions.UserNotExists as e:
            raise UserNotFoundException(email) from e

    async def reset_password(self, password: str, token: str) -> bool:
        """
        Resets the password with the given token.

        Args:
            password: The new password.
            token: The reset password token.

        Returns:
            bool: True if the password is successfully reset, False otherwise.

        Raises:
            InvalidResetPasswordToken: If the reset password token is invalid.
            UserInactive: If the user is inactive.
            InvalidPasswordException: If the password is invalid.
        """

        try:
            await self.user_manager.reset_password(token, password)
            return True
        except exceptions.InvalidResetPasswordToken as e:
            raise exceptions.InvalidResetPasswordToken from e
        except exceptions.UserInactive as e:
            raise exceptions.UserInactive from e
        except exceptions.InvalidPasswordException as e:
            raise exceptions.InvalidPasswordException from e
