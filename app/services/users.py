from fastapi import Request
from app import models, repository as repo
from app.logger import get_logger
from app.schemas import UserCreate, EmailStr, UserUpdate
from fastapi_users import exceptions
from app.auth_manager import UserManager
from app.utils.displayname_generator import generate_displayname
from app.utils.enums import EmailVerificationStatus
from app import database
from app.utils.exceptions import (
    PasswordsDontMatchException,
    UserAlreadyExistsException,
    UserNotFoundException,
)

logger = get_logger(__name__)


class UserService:
    def __init__(self):
        self.user_manager = self._get_user_manager()

    def _get_user_manager(self):
        user_db = database.SQLAlchemyUserDatabase(
            database.db.session, models.User, models.OAuthAccount
        )
        return UserManager(user_db)

    async def delete_self(self, current_user: models.User) -> bool:
        logger.info("Deleting user %s", current_user.id)
        await repo.delete(current_user)
        return True

    async def update_user(self, user: models.User) -> bool:
        logger.info("Updating user %s", user.id)
        return await self.user_manager.update(UserUpdate(), user)

    async def create_user(
        self,
        email: str,
        password: str,
        displayname: str = "",
        is_verified: bool = False,
        is_superuser: bool = False,
        request: Request = None,
    ) -> bool:
        logger.info("Creating new user with email %s", email)

        if not displayname:
            displayname = generate_displayname()

        try:
            return await self.user_manager.create(
                UserCreate(
                    email=email,
                    displayname=displayname,
                    password=password,
                    is_superuser=is_superuser,
                    is_verified=is_verified,
                ),
                request=request,
            )
        except exceptions.UserAlreadyExists:
            logger.warning("User with email %s already exists", email)
            return None

    async def validate_new_user(self, email):
        logger.info("Validating new user with email %s", email)
        try:
            existing_user = await self.user_manager.get_by_email(email)
        except exceptions.UserNotExists:
            existing_user = None

        if existing_user is not None:
            logger.warning("User with email %s already exists", email)
            raise UserAlreadyExistsException()

    async def verify_email(self, token: str) -> EmailVerificationStatus:
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
