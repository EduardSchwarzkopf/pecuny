from typing import List

from fastapi import Depends, status
from fastapi.exceptions import HTTPException

from app import schemas
from app import transaction_manager as tm
from app.models import User
from app.routers.api.users import current_active_user
from app.services import accounts as service
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/accounts", tags=["Accounts"])
ResponseModel = schemas.AccountData


@router.get("/", response_model=List[ResponseModel])
async def api_get_accounts(current_user: User = Depends(current_active_user)):
    """
    Retrieves a list of accounts.

    Args:
        current_user: The current active user.

    Returns:
        List[response_model]: A list of account information.
    """

    return await service.get_accounts(current_user)


@router.get("/{account_id}", response_model=ResponseModel)
async def api_get_account(
    account_id: int, current_user: User = Depends(current_active_user)
):
    """
    Retrieves an account by ID.

    Args:
        account_id: The ID of the account.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved account information.

    Raises:
        HTTPException: If the account is not found.
    """

    account = await service.get_account(current_user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    return account


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def api_create_account(
    account: schemas.Account, current_user: User = Depends(current_active_user)
):
    """
    Creates a new account.

    Args:
        account: The account information.
        current_user: The current active user.

    Returns:
        ResponseModel: The created account information.
    """

    account = await tm.transaction(service.create_account, current_user, account)
    return account


@router.put("/{account_id}", response_model=ResponseModel)
async def api_update_account(
    account_id: int,
    account_data: schemas.AccountUpdate,
    current_user: User = Depends(current_active_user),
):
    """
    Updates an account.

    Args:
        account_id: The ID of the account.
        account_data: The updated account data.
        current_user: The current active user.

    Returns:
        ResponseModel: The updated account information.
    """

    return await tm.transaction(
        service.update_account, current_user, account_id, account_data
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_account(
    account_id: int, current_user: User = Depends(current_active_user)
):
    """
    Deletes an account.

    Args:
        account_id: The ID of the account.
        current_user: The current active user.

    Returns:
        None

    Raises:
        HTTPException: If the account is not found.
    """

    result = await tm.transaction(service.delete_account, current_user, account_id)
    if result:
        return None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
