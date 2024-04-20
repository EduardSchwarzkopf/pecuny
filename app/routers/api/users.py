from fastapi import Depends, HTTPException, Response, status

from app import schemas
from app import transaction_manager as tm
from app.auth_manager import current_active_verified_user
from app.models import User
from app.services.users import UserService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/users", tags=["Users"])
ResponseModel = schemas.UserRead


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_me(
    current_user: User = Depends(current_active_verified_user),
    service: UserService = Depends(UserService),
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
