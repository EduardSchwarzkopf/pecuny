from fastapi import Request
from fastapi_users import exceptions

from app import database, models
from app import repository as repo
from app.auth_manager import UserManager
from app.database import db
from app.logger import get_logger
from app.schemas import EmailStr, UserCreate, UserUpdate
from app.utils.dataclasses_utils import CreateUserData
from app.utils.displayname_generator import generate_displayname
from app.utils.enums import EmailVerificationStatus
from app.utils.exceptions import UserAlreadyExistsException, UserNotFoundException

logger = get_logger(__name__)


class UserService:
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

    def __init__(self):
        """
        Initializes the UserService.

        Args:
            self: The UserService instance.

        Returns:
            None
        """

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

        logger.info("Deleting user %s", current_user.id)
        await repo.delete(current_user)
        return True

    async def update_user(self, user: models.User) -> bool:
        """
        Updates a user.

        Args:
            user: The user object.

        Returns:
            bool: True if the user is successfully updated, False otherwise.
        """

        logger.info("Updating user %s", user.id)
        return await self.user_manager.update(UserUpdate(), user)

    async def create_user(
        self,
        user_data: CreateUserData,
        request: Request = None,
    ) -> bool:
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

        logger.info("Creating new user with email %s", user_data.email)

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
                ),
                request=request,
            )
        except exceptions.UserAlreadyExists:
            logger.warning("User with email %s already exists", user_data.email)
            return None

    async def validate_new_user(self, email):
        """
        Validates a new user with the given email.

        Args:
            email: The email of the user.

        Returns:
            None

        Raises:
            UserAlreadyExistsException: If a user with the given email already exists.
        """

        logger.info("Validating new user with email %s", email)
        try:
            existing_user = await self.user_manager.get_by_email(email)
        except exceptions.UserNotExists:
            existing_user = None

        if existing_user is not None:
            logger.warning("User with email %s already exists", email)
            raise UserAlreadyExistsException()

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

        logger.info("Verifying email with token %s", token)
        try:
            await self.user_manager.verify(token)
            return EmailVerificationStatus.VERIFIED
        except exceptions.InvalidVerifyToken:
            logger.warning("Invalid token for email verification: %s", token)
            return EmailVerificationStatus.INVALID_TOKEN
        except exceptions.UserAlreadyVerified:
            logger.warning("User already verified for token: %s", token)
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

        logger.info("Processing forgot password for email %s", email)
        try:
            existing_user = await self.user_manager.get_by_email(email)
            if existing_user is None:
                logger.warning("No user found with email %s", email)
                raise UserNotFoundException()
            await self.user_manager.forgot_password(existing_user)
        except exceptions.UserNotExists as e:
            logger.warning("No user found with email %s", email)
            raise UserNotFoundException from e

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

        logger.info("Resetting password with token %s", token)
        try:
            await self.user_manager.reset_password(token, password)
            return True
        except exceptions.InvalidResetPasswordToken as e:
            logger.warning("Invalid reset password token: %s", token)
            raise exceptions.InvalidResetPasswordToken from e
        except exceptions.UserInactive as e:
            logger.warning("User is inactive for token: %s", token)
            raise exceptions.UserInactive from e
        except exceptions.InvalidPasswordException as e:
            logger.warning("Invalid password for token: %s", token)
            raise exceptions.InvalidPasswordException from e
