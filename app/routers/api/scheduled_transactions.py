from datetime import datetime

from fastapi import Depends, Response, status
from fastapi.exceptions import HTTPException

from app import schemas
from app import transaction_manager as tm
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.scheduled_transactions import ScheduledTransactionService
from app.utils import APIRouterExtended

router = APIRouterExtended(
    prefix="/scheduled-transactions", tags=["Scheduled Transactions"]
)
ResponseModel = schemas.ScheduledTransactionData


@router.get("/", response_model=list[ResponseModel])
async def api_get_transactions(
    account_id: int,
    date_start: datetime,
    date_end: datetime,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Retrieves a list of transactions.

    Args:
        account_id: The ID of the account.
        date_start: The start date for filtering transactions.
        date_end: The end date for filtering transactions.
        current_user: The current active user.

    Returns:
        list[response_model]: A list of transaction information.

    Raises:
        HTTPException: If the account is not found.
    """

    return await service.get_transaction_list(
        current_user, account_id, date_start, date_end
    )


@router.get("/{transaction_id}", response_model=ResponseModel)
async def api_get_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Retrieves a scheduled transaction by ID.

    Args:
        transaction_id: The ID of the scheduled transaction.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved scheduled transaction information.

    Raises:
        HTTPException: If the scheduled transaction is not found.
    """

    transaction = await service.get_transaction(current_user, transaction_id)

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled transaction not found"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def api_create_transaction(
    transaction_information: schemas.TransactionCreate,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Creates a new scheduled transaction.

    Args:
        transaction_information: The information of the scheduled transaction.
        current_user: The current active user.

    Returns:
        ResponseModel: The created scheduled transaction information.

    Raises:
        HTTPException: If the scheduled transaction is not created.
    """

    transaction = await tm.transaction(
        service.create_scheduled_transaction, current_user, transaction_information
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Scheduled transaction not created",
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Deletes a transaction.

    Args:
        transaction_id: The ID of the transaction.
        current_user: The current active user.

    Returns:
        Response: A response indicating the success or failure of the deletion.

    Raises:
        HTTPException: If the transaction is not found.
    """

    result = await tm.transaction(
        service.delete_scheduled_transaction, current_user, transaction_id
    )
    if result:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content="Transaction deleted successfully",
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
    )
