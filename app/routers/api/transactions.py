from datetime import datetime

from fastapi import Depends, status

from app import schemas
from app import session_transaction_manager as tm
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.transactions import TransactionService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/transactions", tags=["Transactions"])

# pylint: disable=duplicate-code


@router.get("/", response_model=list[schemas.TransactionResponse])
async def api_get_transactions(
    wallet_id: int,
    date_start: datetime,
    date_end: datetime,
    current_user: User = Depends(current_active_verified_user),
    service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Retrieves a list of transactions.

    Args:
        wallet_id: The ID of the wallet.
        date_start: The start date for filtering transactions.
        date_end: The end date for filtering transactions.
        current_user: The current active user.

    Returns:
        list[schemas.TransactionResponse]: A list of transaction information.

    Raises:
        HTTPException: If the wallet is not found.
    """

    return await service.get_transaction_list(
        current_user, wallet_id, date_start, date_end
    )


@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
async def api_get_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Retrieves a transaction by ID.

    Args:
        transaction_id: The ID of the transaction.
        current_user: The current active user.

    Returns:
        schemas.TransactionResponse: The retrieved transaction information.

    Raises:
        HTTPException: If the transaction is not found.
    """

    return await service.get_transaction(current_user, transaction_id)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionResponse
)
async def api_create_transaction(
    transaction_information: schemas.TransactionInformationCreate,
    current_user: User = Depends(current_active_verified_user),
    service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Creates a new transaction.

    Args:
        transaction_information: The information of the transaction.
        current_user: The current active user.

    Returns:
        schemas.TransactionResponse: The created transaction information.

    Raises:
        HTTPException: If the transaction is not created.
    """

    transaction_data = schemas.TransactionData(**transaction_information.model_dump())

    async with tm.transaction():
        return await service.create_transaction(current_user, transaction_data)


@router.post("/{transaction_id}", response_model=schemas.TransactionResponse)
async def api_update_transaction(
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
    current_user: User = Depends(current_active_verified_user),
    service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Updates a transaction.

    Args:
        transaction_id: The ID of the transaction.
        transaction_information: The updated transaction information.
        current_user: The current active user.

    Returns:
        schemas.TransactionResponse: The updated transaction information.

    Raises:
        HTTPException: If the transaction is not found.
    """

    async with tm.transaction():
        transaction = await service.update_transaction(
            current_user,
            transaction_id,
            transaction_information,
        )

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_transaction(
    transaction_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: TransactionService = Depends(TransactionService.get_instance),
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

    async with tm.transaction():
        return await service.delete_transaction(current_user, transaction_id)
