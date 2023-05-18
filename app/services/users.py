from app import models, repository as repo
from app.schemas import UserCreate
from fastapi_users.exceptions import UserAlreadyExists
from app.auth_manager import UserManager


async def delete_self(current_user: models.User) -> bool:
    await repo.delete(current_user)

    return True


async def create_user(
    user_manager: UserManager,
    email: str,
    displayname: str,
    password: str,
    is_superuser: bool = False,
):
    try:
        return await user_manager.create(
            UserCreate(
                email=email,
                displayname=displayname,
                password=password,
                is_superuser=is_superuser,
            )
        )
    except UserAlreadyExists:
        return None
