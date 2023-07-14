from app import models, repository as repo
from app.schemas import UserCreate, EmailStr, UserUpdate
from fastapi_users import exceptions
from app.auth_manager import UserManager
from app.utils.enums import EmailVerificationStatus
from app import database
from app.utils.exceptions import (
    PasswordsDontMatchException,
    UserAlreadyExistsException,
    UserNotFoundException,
)


class UserService:
    def __init__(self):
        self.user_manager = self._get_user_manager()

    def _get_user_manager(self):
        user_db = database.SQLAlchemyUserDatabase(
            database.db.session, models.User, models.OAuthAccount
        )
        return UserManager(user_db)

    async def delete_self(self, current_user: models.User) -> bool:
        await repo.delete(current_user)
        return True

    async def update_user(self, user: models.User) -> bool:
        return await self.user_manager.update(UserUpdate(), user)

    async def create_user(
        self,
        email: str,
        displayname: str,
        password: str,
        is_verified: bool = False,
        is_superuser: bool = False,
    ) -> bool:
        try:
            return await self.user_manager.create(
                UserCreate(
                    email=email,
                    displayname=displayname,
                    password=password,
                    is_superuser=is_superuser,
                    is_verified=is_verified,
                )
            )
        except exceptions.UserAlreadyExists:
            return None

    async def validate_new_user(self, email, password, password_confirm):
        try:
            existing_user = await self.user_manager.get_by_email(email)
        except exceptions.UserNotExists:
            existing_user = None

        if existing_user is not None:
            raise UserAlreadyExistsException()

        if password != password_confirm:
            raise PasswordsDontMatchException()

    async def verify_email(self, token: str) -> EmailVerificationStatus:
        try:
            await self.user_manager.verify(token)
            return EmailVerificationStatus.VERIFIED
        except exceptions.InvalidVerifyToken:
            return EmailVerificationStatus.INVALID_TOKEN
        except exceptions.UserAlreadyVerified:
            return EmailVerificationStatus.ALREADY_VERIFIED

    async def forgot_password(self, email: EmailStr) -> None:
        try:
            existing_user = await self.user_manager.get_by_email(email)
            if existing_user is None:
                raise UserNotFoundException()
            await self.user_manager.forgot_password(existing_user)
        except exceptions.UserNotExists as e:
            raise UserNotFoundException from e

    async def reset_password(self, password: str, token: str) -> bool:
        try:
            await self.user_manager.reset_password(token, password)
            return True
        except exceptions.InvalidResetPasswordToken as e:
            raise exceptions.InvalidResetPasswordToken from e
        except exceptions.UserInactive as e:
            raise exceptions.UserInactive from e
        except exceptions.InvalidPasswordException as e:
            raise exceptions.InvalidPasswordException from e
