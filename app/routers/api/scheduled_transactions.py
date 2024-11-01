from fastapi import Depends, status

from app import schemas
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.scheduled_transactions import ScheduledTransactionService
from app.utils import APIRouterExtended

router = APIRouterExtended(
    prefix="/scheduled-transactions", tags=["Scheduled Transactions"]
)
ResponseModel = schemas.ScheduledTransaction

# pylint: disable=duplicate-code


@router.get("/", response_model=list[ResponseModel])
async def api_get_scheduled_transactions(
    wallet_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Retrieves a list of transactions.

    Args:
        wallet_id: The ID of the wallet.
        date_start: The start date for filtering transactions.
        date_end: The end date for filtering transactions.
        current_user: The current active user.

    Returns:
        list[response_model]: A list of transaction information.

    Raises:
        HTTPException: If the wallet is not found.
    """

    return await service.get_scheduled_transaction_list(current_user, wallet_id)


@router.get("/{transaction_id}", response_model=ResponseModel)
async def api_get_scheduled_transaction(
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

    return await service.get_scheduled_transaction(current_user, transaction_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def api_create_scheduled_transaction(
    transaction_information: schemas.ScheduledTransactionInformationCreate,
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

    return await service.create_scheduled_transaction(
        current_user, transaction_information
    )


@router.post("/{transaction_id}", response_model=ResponseModel)
async def api_update_scheduled_transaction(
    transaction_id: int,
    transaction_information: schemas.ScheduledTransactionInformtionUpdate,
    current_user: User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Update a scheduled transaction via the API.

    Args:
        transaction_id: The ID of the transaction to update.
        transaction_information: The updated information for the transaction.
        current_user: The current authenticated user.
        service: The service for handling scheduled transactions.

    Returns:
        The updated scheduled transaction if successful.

    Raises:
        HTTPException: If the scheduled transaction update fails.
    """

    return await service.update_scheduled_transaction(
        current_user,
        transaction_id,
        transaction_information,
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_scheduled_transaction(
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

    return await service.delete_scheduled_transaction(current_user, transaction_id)
