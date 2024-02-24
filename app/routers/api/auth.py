from fastapi import Depends, HTTPException, Request, status

from app import schemas
from app.services.users import UserService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/auth", tags=["Auth"])


# TODO: Create a single place for this function
# it can be found on several places now
async def get_user_service() -> UserService:
    """
    Returns an instance of the UserService class.

    Returns:
        UserService: An instance of the UserService class.
    """

    return UserService()


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserRead
)
async def api_create_user(
    user: schemas.UserCreate,
    request: Request,
    service: UserService = Depends(get_user_service),
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
        user.email, user.password, user.displayname, request=request
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred while processing your request",
        )

    return user
