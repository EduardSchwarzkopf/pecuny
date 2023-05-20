from typing import List
from fastapi import Depends, APIRouter, status, Response
from fastapi.exceptions import HTTPException

from app import schemas, transaction_manager as tm
from app.services import accounts as service
from app.routers.api.users import current_active_user
from app.models import User

router = APIRouter()
response_model = schemas.AccountData


@router.get("/", response_model=List[response_model])
async def get_accounts(current_user: User = Depends(current_active_user)):
    return await service.get_accounts(current_user)


@router.get("/{account_id}", response_model=response_model)
async def get_account(
    account_id: int, current_user: User = Depends(current_active_user)
):
    account = await service.get_account(current_user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    return account


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
async def create_account(
    account: schemas.Account, current_user: User = Depends(current_active_user)
):
    account = await tm.transaction(service.create_account, current_user, account)
    return account


@router.put("/{account_id}", response_model=response_model)
async def update_account(
    account_id: int,
    account_data: schemas.AccountUpdate,
    current_user: User = Depends(current_active_user),
):
    return await tm.transaction(
        service.update_account, current_user, account_id, account_data
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int, current_user: User = Depends(current_active_user)
):
    result = await tm.transaction(service.delete_account, current_user, account_id)
    if result:
        return None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
