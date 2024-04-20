import csv
import decimal
from io import StringIO

from fastapi import BackgroundTasks, Depends, File, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from pydantic import ValidationError

from app import schemas
from app import transaction_manager as tm
from app.background_tasks import import_transactions
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.accounts import AccountService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/accounts", tags=["Accounts"])
ResponseModel = schemas.AccountData


@router.get("/", response_model=list[ResponseModel])
async def api_get_accounts(
    current_user: User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
):
    """
        Retrieves a list of accounts.

        Args:
            current_user: The current active user.

    Returns:
        list[response_model]: A list of account information.
    """

    return await service.get_accounts(current_user)


@router.get("/{account_id}", response_model=ResponseModel)
async def api_get_account(
    account_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
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
    account: schemas.Account,
    current_user: User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
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


@router.post("/{account_id}", response_model=ResponseModel)
async def api_update_account(
    account_id: int,
    account_data: schemas.AccountUpdate,
    current_user: User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
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
    account_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
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


@router.post("/{account_id}/import")
async def api_import_transactions(
    account_id: int,
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
            transaction_list.append(
                schemas.TransactionInformationCreate(account_id=account_id, **row)
            )
        except ValidationError as e:
            first_error = e.errors()[0]
            custom_error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            raise HTTPException(status_code=400, detail=custom_error_message) from e
        except decimal.InvalidOperation as e:
            msg = f"Invalid value on line {reader.line_num} on value {row['amount']}"
            raise HTTPException(status_code=400, detail=msg) from e

    background_tasks.add_task(import_transactions, current_user, transaction_list)

    return Response(status_code=status.HTTP_202_ACCEPTED)
