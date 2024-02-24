from datetime import datetime
from typing import List

from fastapi import Depends, Response, status
from fastapi.exceptions import HTTPException

from app import schemas
from app import transaction_manager as tm
from app.models import User
from app.routers.api.users import current_active_user
from app.services import transactions as service
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/transactions", tags=["Transactions"])
response_model = schemas.Transaction


@router.get("/", response_model=List[response_model])
async def api_get_transactions(
    account_id: int,
    date_start: datetime,
    date_end: datetime,
    current_user: User = Depends(current_active_user),
):
    return await service.get_transaction_list(
        current_user, account_id, date_start, date_end
    )


@router.get("/{transaction_id}", response_model=response_model)
async def api_get_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_user),
):
    transaction = await tm.transaction(
        service.get_transaction, current_user, transaction_id
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
async def api_create_transaction(
    transaction_information: schemas.TransactionInformationCreate,
    current_user: User = Depends(current_active_user),
):
    transaction = await tm.transaction(
        service.create_transaction, current_user, transaction_information
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Transaction not created"
    )


@router.post("/{transaction_id}", response_model=response_model)
async def api_update_transaction(
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
    current_user: User = Depends(current_active_user),
):
    transaction = await tm.transaction(
        service.update_transaction,
        current_user,
        transaction_id,
        transaction_information,
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_account(
    transaction_id: int, current_user: User = Depends(current_active_user)
):
    result = await tm.transaction(
        service.delete_transaction, current_user, transaction_id
    )
    if result:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content="Transaction deleted successfully",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
