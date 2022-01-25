from typing import List
from fastapi import Depends, APIRouter, status
from fastapi.exceptions import HTTPException
from .. import models, schemas, oauth2
from ..transaction_manager import transaction as tm
from ..services import accounts as service


router = APIRouter(prefix="/accounts", tags=["Accounts"])
response_model = schemas.Accounts


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
    account = service.get_account(account_id)
    return account


@router.post("/", response_model=response_model)
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


@router.get("/{account_id}", methods=["DELETE"])
def delete(
    account_id: int, current_user: models.User = Depends(oauth2.get_current_user)
):
    result = tm.transaction(service.delete, account_id)
    return result
