import contextlib
from app import models, repository as repo
from app.schemas import UserCreate, EmailStr
from fastapi_users import exceptions
from app.auth_manager import UserManager
from app.utils.enums import EmailVerificationStatus


class UserService:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    async def delete_self(self, current_user: models.User) -> bool:
        await repo.delete(current_user)
        return True

    async def create_user(
        self, email: str, displayname: str, password: str, is_superuser: bool = False
    ) -> bool:
        try:
            return await self.user_manager.create(
                UserCreate(
                    email=email,
                    displayname=displayname,
                    password=password,
                    is_superuser=is_superuser,
                )
            )
        except exceptions.UserAlreadyExists:
            return None

    async def verify_email(self, token: str) -> EmailVerificationStatus:
        try:
            await self.user_manager.verify(token)
            return EmailVerificationStatus.VERIFIED
        except exceptions.InvalidVerifyToken:
            return EmailVerificationStatus.INVALID_TOKEN
        except exceptions.UserAlreadyVerified:
            return EmailVerificationStatus.ALREADY_VERIFIED

    async def forgot_password(self, email: EmailStr) -> None:
        with contextlib.suppress(exceptions.UserNotExists):
            existing_user = await self.user_manager.get_by_email(email)
            await self.user_manager.forgot_password(existing_user)
        return None

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
