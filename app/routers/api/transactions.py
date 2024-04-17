import csv
import decimal
from datetime import datetime
from io import StringIO

from fastapi import (BackgroundTasks, Depends, File, Response, UploadFile,
                     status)
from fastapi.exceptions import HTTPException
from pydantic import ValidationError

from app import schemas
from app import transaction_manager as tm
from app.models import User
from app.routers.api.background_tasks import import_transactions
from app.routers.api.users import current_active_verified_user
from app.services.transactions import TransactionService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/transactions", tags=["Transactions"])
ResponseModel = schemas.Transaction
service = TransactionService()


@router.get("/", response_model=list[ResponseModel])
async def api_get_transactions(
    account_id: int,
    date_start: datetime,
    date_end: datetime,
    current_user: User = Depends(current_active_verified_user),
):
    """
    Retrieves a list of transactions.

    Args:
        account_id: The ID of the account.
        date_start: The start date for filtering transactions.
        date_end: The end date for filtering transactions.
        current_user: The current active user.

    Returns:
        list[ResponseModel]: A list of transaction information.

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
):
    """
    Retrieves a transaction by ID.

    Args:
        transaction_id: The ID of the transaction.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved transaction information.

    Raises:
        HTTPException: If the transaction is not found.
    """

    transaction = await tm.transaction(
        service.get_transaction, current_user, transaction_id
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def api_create_transaction(
    transaction_information: schemas.TransactionInformationCreate,
    current_user: User = Depends(current_active_verified_user),
):
    """
    Creates a new transaction.

    Args:
        transaction_information: The information of the transaction.
        current_user: The current active user.

    Returns:
        ResponseModel: The created transaction information.

    Raises:
        HTTPException: If the transaction is not created.
    """

    transaction = await tm.transaction(
        service.create_transaction, current_user, transaction_information
    )

    if transaction:
        return transaction

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Transaction not created"
    )


@router.post("/import")
async def create_items(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_verified_user),
    file: UploadFile = File(...),
):
    """
    Handles the creation of items from a CSV file upload.

    Args:
        current_user: The current authenticated and verified user.
        file: The uploaded CSV file.

    Returns:
        Response: HTTP response indicating the success of the import operation.
    Raises:
        HTTPException: If the file type is invalid, file is empty,
        decoding error occurs, validation fails, or import fails.
    """

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        contents_str = contents.decode()
        csv_file = StringIO(contents_str)
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=e.reason) from e

    reader = csv.DictReader(csv_file, delimiter=";")

    transaction_list = []
    for row in reader:

        try:
            transaction_list.append(schemas.TransactionInformationCreate(**row))
        except ValidationError as e:
            first_error = e.errors()[0]
            custom_error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            raise HTTPException(status_code=400, detail=custom_error_message) from e
        except decimal.InvalidOperation as e:
            msg = f"Invalid value on line {reader.line_num} on value {row["amount"]}"
            raise HTTPException(status_code=400, detail=msg) from e

    background_tasks.add_task(import_transactions, current_user, transaction_list)

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/{transaction_id}", response_model=ResponseModel)
async def api_update_transaction(
    transaction_id: int,
    transaction_information: schemas.TransactionInformtionUpdate,
    current_user: User = Depends(current_active_verified_user),
):
    """
    Updates a transaction.

    Args:
        transaction_id: The ID of the transaction.
        transaction_information: The updated transaction information.
        current_user: The current active user.

    Returns:
        ResponseModel: The updated transaction information.

    Raises:
        HTTPException: If the transaction is not found.
    """

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
async def api_delete_transaction(
    transaction_id: int, current_user: User = Depends(current_active_verified_user)
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
