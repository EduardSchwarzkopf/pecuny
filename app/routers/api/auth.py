from fastapi import Depends, Request, status, HTTPException
from app import schemas
from app.services.users import UserService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/auth", tags=["Auth"])


async def get_user_service() -> UserService:
    return UserService()


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserRead
)
async def api_create_user(
    user: schemas.UserCreate,
    request: Request,
    service: UserService = Depends(get_user_service),
):
    user = await service.create_user(
        user.email, user.password, user.displayname, request=request
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred while processing your request",
        )

    return user
