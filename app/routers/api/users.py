from fastapi import Depends, APIRouter, status, Response, HTTPException

from app import transaction_manager as tm
from app.services import users as service
from app.models import User
from app.auth_manager import current_active_user

router = APIRouter()


# override fastapi_users functionality
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(current_user: User = Depends(current_active_user)):
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
