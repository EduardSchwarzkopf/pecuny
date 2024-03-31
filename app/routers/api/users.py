from fastapi import Depends, HTTPException, Response, status

from app import schemas
from app import transaction_manager as tm
from app.auth_manager import current_active_user
from app.authentication.dependencies import get_user_service
from app.models import User
from app.services.users import UserService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/users", tags=["Users"])


@router.get("/me", status_code=status.HTTP_200_OK, response_model=schemas.UserRead)
async def api_get_me(current_user: User = Depends(current_active_user)):
    return current_user


@router.post("/me", status_code=status.HTTP_200_OK)
async def api_update_me(
    user_data: schemas.UserUpdate,
    current_user: User = Depends(current_active_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(current_user, user_data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_me(
    current_user: User = Depends(current_active_user),
    service: UserService = Depends(get_user_service),
):
    """
    Deletes the current user.

    Args:
        current_user: The current active user.

    Returns:
        Response: A response indicating the success or failure of the deletion.

    Raises:
        HTTPException: If the transaction is not found.
    """

    result = await tm.transaction(service.delete_self, current_user)

    if result:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content="User deleted successfully",
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
