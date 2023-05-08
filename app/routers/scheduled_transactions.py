from typing import List
from datetime import datetime
from fastapi import Depends, APIRouter, status
from fastapi.exceptions import HTTPException
from .. import schemas, transaction_manager as tm
from ..services import scheduled_transactions as service
from app.routers.users import current_active_user
from app.database import User

router = APIRouter()
response_model = schemas.ScheduledTransactionData


@router.get("/", response_model=List[response_model])
async def get_transactions(
    account_id: int,
    date_start: datetime,
    date_end: datetime,
    current_user: User = Depends(current_active_user),
):
    return await service.get_transaction_list(
        current_user, account_id, date_start, date_end
    )


@router.get("/{transaction_id}", response_model=response_model)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_user),
):

    transaction = await service.get_transaction(current_user, transaction_id)

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled transaction not found"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
async def create_transaction(
    transaction_information: schemas.ScheduledTransactionInformationCreate,
    current_user: User = Depends(current_active_user),
):
    transaction = await tm.transaction(
        service.create_scheduled_transaction, current_user, transaction_information
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Scheduled transaction not created",
    )
