import calendar
from datetime import datetime
from itertools import groupby

from fastapi import Cookie, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette_wtf import csrf_protect

from app import models, schemas
from app.auth_manager import current_active_verified_user
from app.routers.dashboard import router as dashboard_router
from app.services.transactions import TransactionService
from app.services.wallets import WalletService
from app.utils import PageRouter
from app.utils.enums import FeedbackType
from app.utils.file_utils import process_csv_file
from app.utils.template_utils import (
    add_breadcrumb,
    calculate_financial_summary,
    render_template,
    set_feedback,
)
from app.utils.wallet_utils import get_wallet_list_template

PREFIX = f"{dashboard_router.prefix}/wallets"
router = PageRouter(prefix=PREFIX, tags=["Wallets"])


async def handle_wallet_route(
    request: Request, user: models.User, wallet_id: int, create_link=True
) -> models.Wallet:
    """
    Handles the wallet route.

    Args:
        request: The request object.
        user: The current active user.
        wallet_id: The ID of the wallet.
        create_link: Whether to create a link for the wallet breadcrumb (default is True).

    Returns:
        Wallet: The wallet object.
    """

    service = WalletService()
    wallet = await service.get_wallet(user, wallet_id)

    add_breadcrumb(request, "Wallets", PREFIX)
    wallet_url = f"{PREFIX}/{wallet_id}" if create_link else ""
    add_breadcrumb(request, wallet.label, wallet_url)

    return wallet


@router.get("/", response_class=HTMLResponse)
async def page_list_wallets(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the list wallets page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered list wallets page.
    """

    return await get_wallet_list_template(
        user, "pages/dashboard/page_list_wallets.html", request
    )


async def max_wallets_reached(
    user: models.User, request: Request, service: WalletService
) -> RedirectResponse:
    """
    Checks if the maximum number of wallets has been reached for a user.

    Args:
        user: The user object.
        request: The request object.

    Returns:
        RedirectResponse: A redirect response to the list wallets page
            if the maximum number of wallets has been reached.
    """

    if await service.check_max_wallets(user):
        set_feedback(request, FeedbackType.ERROR, "Maximum number of wallets reached")
        return RedirectResponse(
            router.url_path_for("page_list_wallets"),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@csrf_protect
@router.get("/add", response_class=HTMLResponse)
async def page_create_wallet_form(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Renders the create wallet form page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered create wallet form page.
    """

    if response := await max_wallets_reached(user, request, service):
        return response

    form = schemas.CreateWalletForm(request)

    return render_template(
        "pages/dashboard/page_form_wallet.html",
        request,
        {"form": form, "action_url": router.url_path_for("page_create_wallet")},
    )


@csrf_protect
@router.post("/add")
async def page_create_wallet(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Creates a new wallet.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the list wallets page.
    """

    if response := await max_wallets_reached(user, request, service):
        return response

    form = await schemas.CreateWalletForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_wallet.html",
            request,
            {"form": form, "action_url": router.url_path_for("page_create_wallet")},
        )

    wallet = schemas.Wallet(**form.data)

    await service.create_wallet(user, wallet)

    return RedirectResponse(router.url_path_for("page_list_wallets"), status_code=302)


@router.get("/{wallet_id}")
async def page_get_wallet(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
    date_start: datetime = Cookie(None),
    date_end: datetime = Cookie(None),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Renders the wallet details page.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.
        date_start: The start date for filtering transactions (optional).
        date_end: The end date for filtering transactions (optional).

    Returns:
        TemplateResponse: The rendered wallet details page.
    """

    wallet = await handle_wallet_route(request, user, wallet_id, False)

    if date_start is None:
        date_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

    if date_end is None:
        last_day = calendar.monthrange(date_start.year, date_start.month)[1]
        date_end = datetime.now().replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )

    transaction_list: list[models.Transaction] = (
        await transaction_service.get_transaction_list(
            user, wallet_id, date_start, date_end
        )
    )

    financial_summary = calculate_financial_summary(transaction_list)
    expenses = financial_summary.expenses
    income = financial_summary.income
    total = financial_summary.total

    filtered_transaction_list = [tx for tx in transaction_list if tx is not None]
    filtered_transaction_list.sort(key=lambda x: x.information.date, reverse=True)

    transaction_list_grouped = [
        {"date": date, "transactions": list(transactions)}
        for date, transactions in groupby(
            filtered_transaction_list, key=lambda x: x.information.date
        )
    ]

    return render_template(
        "pages/dashboard/page_single_wallet.html",
        request,
        {
            "wallet": wallet,
            "transaction_list_grouped": transaction_list_grouped,
            "date_picker_form": schemas.DatePickerForm(request),
            "expenses": expenses,
            "income": income,
            "total": total,
        },
    )


@router.get("/{wallet_id}/edit")
async def page_update_wallet_form(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the update wallet form page.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered update wallet form page.
    """

    wallet = await handle_wallet_route(request, user, wallet_id)

    form = schemas.UpdateWalletForm(request, data=wallet.__dict__)

    return render_template(
        "pages/dashboard/page_form_wallet.html",
        request,
        {
            "wallet_id": wallet_id,
            "form": form,
            "action_url": router.url_path_for(
                "page_update_wallet", wallet_id=wallet_id
            ),
        },
    )


@csrf_protect
@router.post("/{wallet_id}/delete")
async def page_delete_wallet(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Handles the deletion of an wallet.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the list wallets page.
    """

    await handle_wallet_route(request, user, wallet_id)

    await service.delete_wallet(user, wallet_id)

    return RedirectResponse(router.url_path_for("page_list_wallets"), status_code=302)


@csrf_protect
@router.post("/{wallet_id}/edit")
async def page_update_wallet(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
    service: WalletService = Depends(WalletService.get_instance),
):
    """
    Handles the update of an wallet.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the wallet page.
    """

    wallet = await handle_wallet_route(request, user, wallet_id)

    form = await schemas.UpdateWalletForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_wallet.html",
            request,
            {
                "wallet_id": wallet_id,
                "form": form,
                "action_url": router.url_path_for(
                    "page_update_wallet", wallet_id=wallet_id
                ),
            },
        )

    wallet = schemas.Wallet(**form.data, balance=wallet.balance)

    await service.update_wallet(user, wallet_id, wallet)

    return RedirectResponse(
        router.url_path_for("page_get_wallet", wallet_id=wallet_id), status_code=302
    )


@router.get("/{wallet_id}/import")
async def page_import_transactions_get(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Handles GET requests to import transactions for a specific wallet.

    Args:
        request: The incoming request object.
        wallet_id: The ID of the wallet for which transactions are being imported.
        _user: The current active and verified user.

    Returns:
        The rendered template for importing transactions with the form and action URL.
    """

    form = schemas.ImportTransactionsForm(request)

    await handle_wallet_route(request, user, wallet_id)

    return render_template(
        "pages/dashboard/page_form_import_transactions.html",
        request,
        {
            "form": form,
            "action_url": router.url_path_for(
                "page_import_transactions_post", wallet_id=wallet_id
            ),
        },
    )


@router.post("/{wallet_id}/import")
async def page_import_transactions_post(
    request: Request,
    wallet_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(current_active_verified_user),
):
    """
    Handles the creation of items from a CSV file upload.

    Args:
        current_user: The current authenticated and verified user.
        file: The uploaded CSV file.

    Returns:
        Response: HTTP response indicating the success of the import operation.
    """

    form = await schemas.ImportTransactionsForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_import_transactions.html",
            request,
            {
                "form": form,
                "action_url": router.url_path_for(
                    "page_import_transactions_get", wallet_id=wallet_id
                ),
            },
        )

    await process_csv_file(wallet_id, file, current_user)

    return RedirectResponse(
        router.url_path_for("page_get_wallet", wallet_id=wallet_id), status_code=302
    )
