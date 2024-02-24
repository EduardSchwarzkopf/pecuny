from fastapi import Depends, HTTPException, Response, status

from app import transaction_manager as tm
from app.auth_manager import current_active_user
from app.models import User
from app.services.users import UserService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    """
    Returns an instance of the UserService class.

    Returns:
        UserService: An instance of the UserService class.
    """

    return UserService()


# override fastapi_users functionality
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_me(
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
):
    """
    Deletes the current user.

    Args:
        service: The user service.
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
            content="Transaction deleted successfully",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
