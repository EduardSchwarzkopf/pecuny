from typing import List
from fastapi import Depends, APIRouter, status, Response
from fastapi.exceptions import HTTPException
from .. import models, schemas, oauth2, transaction_manager as tm
from ..services import accounts as service


router = APIRouter(prefix="/accounts", tags=["Accounts"])
response_model = schemas.AccountData


@router.get("/", response_model=List[response_model])
def get_accounts(
    current_user: models.User = Depends(oauth2.get_current_user),
):
    accounts = service.get_accounts(current_user)
    return accounts


@router.get("/{account_id}", response_model=response_model)
def get_account(
    account_id: int,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    account = service.get_account(current_user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    return account


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
def create_account(
    account: schemas.Account,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    account = tm.transaction(service.create_account, current_user, account)
    return account


@router.put("/{account_id}")
def update_account(
    account: schemas.Account,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    account = tm.transaction(service.update, data)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int, current_user: models.User = Depends(oauth2.get_current_user)
):
    result = tm.transaction(service.delete_account, current_user, account_id)
    if result:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content="Account deleted successfully",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
