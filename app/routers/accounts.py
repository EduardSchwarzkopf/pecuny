import calendar
from datetime import datetime
from itertools import groupby

from fastapi import BackgroundTasks, Cookie, Depends, File, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette_wtf import csrf_protect

from app import models, schemas
from app import transaction_manager as tm
from app.auth_manager import current_active_verified_user
from app.routers.dashboard import router as dashboard_router
from app.services.accounts import AccountService
from app.services.transactions import TransactionService
from app.utils import PageRouter
from app.utils.account_utils import get_account_list_template
from app.utils.enums import FeedbackType
from app.utils.file_utils import process_csv_file
from app.utils.template_utils import add_breadcrumb, render_template, set_feedback

PREFIX = f"{dashboard_router.prefix}/accounts"
router = PageRouter(prefix=PREFIX, tags=["Accounts"])


async def handle_account_route(
    request: Request, user: models.User, account_id: int, create_link=True
) -> models.Account:
    """
    Handles the account route.

    Args:
        request: The request object.
        user: The current active user.
        account_id: The ID of the account.
        create_link: Whether to create a link for the account breadcrumb (default is True).

    Returns:
        Account: The account object.

    Raises:
        HTTPException: If the account is not found.
    """

    service = AccountService()
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    add_breadcrumb(request, "Accounts", PREFIX)
    account_url = f"{PREFIX}/{account_id}" if create_link else ""
    add_breadcrumb(request, account.label, account_url)

    return account


@router.get("/", response_class=HTMLResponse)
async def page_list_accounts(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the list accounts page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered list accounts page.
    """

    return await get_account_list_template(
        user, "pages/dashboard/page_list_accounts.html", request
    )


async def max_accounts_reached(
    user: models.User, request: Request, service: AccountService
) -> RedirectResponse:
    """
    Checks if the maximum number of accounts has been reached for a user.

    Args:
        user: The user object.
        request: The request object.

    Returns:
        RedirectResponse: A redirect response to the list accounts page
            if the maximum number of accounts has been reached.
    """

    if await service.check_max_accounts(user):
        set_feedback(request, FeedbackType.ERROR, "Maximum number of accounts reached")
        return RedirectResponse(
            router.url_path_for("page_list_accounts"),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@csrf_protect
@router.get("/add", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
):
    """
    Renders the create account form page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered create account form page.
    """

    if response := await max_accounts_reached(user, request, service):
        return response

    form = schemas.CreateAccountForm(request)

    return render_template(
        "pages/dashboard/page_form_account.html",
        request,
        {"form": form, "action_url": router.url_path_for("page_create_account")},
    )


@csrf_protect
@router.post("/add")
async def page_create_account(
    request: Request,
    user: models.User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
):
    """
    Creates a new account.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the list accounts page.
    """

    if response := await max_accounts_reached(user, request, service):
        return response

    form = await schemas.CreateAccountForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_account.html",
            request,
            {"form": form, "action_url": router.url_path_for("page_create_account")},
        )

    account = schemas.Account(**form.data)

    response = await tm.transaction(service.create_account, user, account)

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(router.url_path_for("page_list_accounts"), status_code=302)


@router.get("/{account_id}")
async def page_get_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
    date_start: datetime = Cookie(None),
    date_end: datetime = Cookie(None),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Renders the account details page.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.
        date_start: The start date for filtering transactions (optional).
        date_end: The end date for filtering transactions (optional).

    Returns:
        TemplateResponse: The rendered account details page.
    """

    account = await handle_account_route(request, user, account_id, False)

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
            user, account_id, date_start, date_end
        )
    ) or []

    expenses = 0
    income = 0
    total = 0

    for transaction in transaction_list:
        if transaction.information.amount < 0:
            expenses += transaction.information.amount
        else:
            income += transaction.information.amount

        total += transaction.information.amount

    transaction_list.sort(key=lambda x: x.information.date, reverse=True)

    transaction_list_grouped = [
        {"date": date, "transactions": list(transactions)}
        for date, transactions in groupby(
            transaction_list, key=lambda x: x.information.date
        )
    ]
    return render_template(
        "pages/dashboard/page_single_account.html",
        request,
        {
            "account": account,
            "transaction_list_grouped": transaction_list_grouped,
            "date_picker_form": schemas.DatePickerForm(request),
            "expenses": expenses,
            "income": income,
            "total": total,
        },
    )


@router.get("/{account_id}/edit")
async def page_update_account_form(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the update account form page.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered update account form page.
    """

    account = await handle_account_route(request, user, account_id)

    form = schemas.UpdateAccountForm(request, data=account.__dict__)

    return render_template(
        "pages/dashboard/page_form_account.html",
        request,
        {
            "account_id": account_id,
            "form": form,
            "action_url": router.url_path_for(
                "page_update_account", account_id=account_id
            ),
        },
    )


@csrf_protect
@router.post("/{account_id}/delete")
async def page_delete_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
):
    """
    Handles the deletion of an account.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the list accounts page.
    """

    await handle_account_route(request, user, account_id)

    response = await tm.transaction(service.delete_account, user, account_id)

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(router.url_path_for("page_list_accounts"), status_code=302)


@csrf_protect
@router.post("/{account_id}/edit")
async def page_update_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
    service: AccountService = Depends(AccountService.get_instance),
):
    """
    Handles the update of an account.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the account page.
    """

    account = await handle_account_route(request, user, account_id)

    form = await schemas.UpdateAccountForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_account.html",
            request,
            {
                "account_id": account_id,
                "form": form,
                "action_url": router.url_path_for(
                    "page_update_account", account_id=account_id
                ),
            },
        )

    account = schemas.Account(**form.data, balance=account.balance)

    response = await tm.transaction(service.update_account, user, account_id, account)

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )


@router.get("/{account_id}/import")
async def page_import_transactions_get(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Handles GET requests to import transactions for a specific account.

    Args:
        request: The incoming request object.
        account_id: The ID of the account for which transactions are being imported.
        _user: The current active and verified user.

    Returns:
        The rendered template for importing transactions with the form and action URL.
    """

    form = schemas.ImportTransactionsForm(request)

    await handle_account_route(request, user, account_id)

    return render_template(
        "pages/dashboard/page_form_import_transactions.html",
        request,
        {
            "form": form,
            "action_url": router.url_path_for(
                "page_import_transactions_post", account_id=account_id
            ),
        },
    )


@router.post("/{account_id}/import")
async def page_import_transactions_post(
    request: Request,
    account_id: int,
    background_tasks: BackgroundTasks,
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
    Raises:
        HTTPException: If the file type is invalid, file is empty,
        decoding error occurs, validation fails, or import fails.
    """

    form = await schemas.ImportTransactionsForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_import_transactions.html",
            request,
            {
                "form": form,
                "action_url": router.url_path_for(
                    "page_import_transactions_get", account_id=account_id
                ),
            },
        )

    await process_csv_file(account_id, file, current_user, background_tasks)

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )
