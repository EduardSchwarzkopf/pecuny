import jwt
from app import models, repository as repo
from app.schemas import UserCreate
from fastapi_users import exceptions
from app.auth_manager import UserManager
from app.utils.enums import EmailVerificationStatus


async def delete_self(current_user: models.User) -> bool:
    await repo.delete(current_user)

    return True


async def create_user(
    user_manager: UserManager,
    email: str,
    displayname: str,
    password: str,
    is_superuser: bool = False,
) -> bool:
    try:
        return await user_manager.create(
            UserCreate(
                email=email,
                displayname=displayname,
                password=password,
                is_superuser=is_superuser,
            )
        )
    except exceptions.UserAlreadyExists:
        return None


async def verify_email(
    user_manager: UserManager, token: str
) -> EmailVerificationStatus:
    try:
        await user_manager.verify(token)
        return EmailVerificationStatus.VERIFIED
    except exceptions.InvalidVerifyToken:
        return EmailVerificationStatus.INVALID_TOKEN
    except exceptions.UserAlreadyVerified:
        return EmailVerificationStatus.ALREADY_VERIFIED
