from fastapi import Depends, File, Response, UploadFile, status

from app import schemas
from app import session_transaction_manager as tm
from app.exceptions.http_exceptions import HTTPForbiddenException, HTTPNotFoundException
from app.exceptions.wallet_service_exceptions import (
    WalletAccessDeniedException,
    WalletNotFoundException,
)
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.wallets import WalletService
from app.utils import APIRouterExtended
from app.utils.file_utils import process_csv_file

router = APIRouterExtended(prefix="/wallets", tags=["Wallets"])
ResponseModel = schemas.WalletData


@router.get("/", response_model=list[ResponseModel])
async def api_get_wallets(
    current_user: User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
        Retrieves a list of wallets.

        Args:
            current_user: The current active user.

    Returns:
        list[response_model]: A list of wallet information.
    """

    return await service.get_wallets(current_user)


@router.get("/{wallet_id}", response_model=ResponseModel)
async def api_get_wallet(
    wallet_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Retrieves an wallet by ID.

    Args:
        wallet_id: The ID of the wallet.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved wallet information.

    Raises:
        HTTPException: If the wallet is not found.
    """

    try:
        return await service.get_wallet(current_user, wallet_id)
    except WalletNotFoundException as e:
        raise HTTPNotFoundException() from e
    except WalletAccessDeniedException as e:
        raise HTTPForbiddenException() from e


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel)
async def api_create_wallet(
    wallet: schemas.Wallet,
    current_user: User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Creates a new wallet.

    Args:
        wallet: The wallet information.
        current_user: The current active user.

    Returns:
        ResponseModel: The created wallet information.
    """

    async with tm.transaction():
        return await service.create_wallet(current_user, wallet)


@router.post("/{wallet_id}", response_model=ResponseModel)
async def api_update_wallet(
    wallet_id: int,
    wallet_data: schemas.WalletUpdate,
    current_user: User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Updates an wallet.

    Args:
        wallet_id: The ID of the wallet.
        wallet_data: The updated wallet data.
        current_user: The current active user.

    Returns:
        ResponseModel: The updated wallet information.
    """

    async with tm.transaction():
        try:
            return await service.update_wallet(current_user, wallet_id, wallet_data)
        except WalletNotFoundException as e:
            raise HTTPNotFoundException() from e
        except WalletAccessDeniedException as e:
            raise HTTPForbiddenException() from e


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_wallet(
    wallet_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Deletes an wallet.

    Args:
        wallet_id: The ID of the wallet.
        current_user: The current active user.

    Returns:
        None

    Raises:
        HTTPException: If the wallet is not found.
    """

    async with tm.transaction():
        try:
            return await service.delete_wallet(current_user, wallet_id)
        except WalletNotFoundException as e:
            raise HTTPNotFoundException() from e
        except WalletAccessDeniedException as e:
            raise HTTPForbiddenException() from e


@router.post("/{wallet_id}/import")
async def api_import_transactions(
    wallet_id: int,
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

    await process_csv_file(wallet_id, file, current_user)

    return Response(status_code=status.HTTP_202_ACCEPTED)
