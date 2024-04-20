from fastapi import Depends, HTTPException, Request, status

from app import schemas
from app.services.users import UserService
from app.utils import APIRouterExtended
from app.utils.dataclasses_utils import CreateUserData

router = APIRouterExtended(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserRead
)
async def api_create_user(
    user_data: schemas.UserCreate,
    request: Request,
    service: UserService = Depends(UserService),
):
    """
    Creates a new user.

    Args:
        user: The user information.
        request: The request object.
        service: The user service.

    Returns:
        UserRead: The created user information.
    """

    user = await service.create_user(
        CreateUserData(user_data.email, user_data.password, user_data.displayname),
        request=request,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred while processing your request",
        )

    return user
