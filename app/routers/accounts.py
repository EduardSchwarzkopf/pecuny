from datetime import datetime
import calendar
from itertools import groupby
from fastapi import Request, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette_wtf import csrf_protect
from app.config import settings
from fastapi.exceptions import HTTPException
from starlette import status
from app.utils import PageRouter
from app.utils.enums import FeedbackType
from app.utils.template_utils import (
    group_categories_by_section,
    render_dashboard_template,
    set_feedback,
)
from app import schemas, transaction_manager as tm, models
from app.services import (
    accounts as service,
    transactions as transaction_service,
    categories as category_service,
)
from app.auth_manager import current_active_user

router = PageRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/", response_class=HTMLResponse)
async def page_accounts_list(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    account_list = await service.get_accounts(user)
    return render_dashboard_template(
        "pages/dashboard/page_multiple_accounts.html",
        request,
        {
            "account_list": account_list,
            "max_allowed_accounts": settings.max_allowed_accounts,
        },
    )


def max_accounts_reached(user, request: Request) -> RedirectResponse:
    if service.check_max_accounts(user):
        set_feedback(request, FeedbackType.ERROR, "Maximum number of accounts reached")
        return RedirectResponse(
            router.url_path_for("page_accounts_list"),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@csrf_protect
@router.get("/add", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    if response := max_accounts_reached(user, request):
        return response

    form = await schemas.CreateAccountForm.from_formdata(request)

    return render_dashboard_template(
        "pages/dashboard/page_create_account.html", request, {"form": form}
    )


@csrf_protect
@router.post("/create-account")
async def page_create_account(
    request: Request, user: models.User = Depends(current_active_user)
):
    if response := max_accounts_reached(user, request):
        return response

    form = await schemas.CreateAccountForm.from_formdata(request)

    if not await form.validate_on_submit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Validation error"
        )

    account = schemas.Account(**form.data)

    response = await tm.transaction(service.create_account, user, account)

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_create_account_form"), status_code=302
    )


@router.get("/{account_id}")
async def page_get_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
    date_start: datetime = Cookie(None),
    date_end: datetime = Cookie(None),
):
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    if date_start is None:
        date_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

    if date_end is None:
        last_day = calendar.monthrange(date_start.year, date_start.month)[1]
        date_end = datetime.now().replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )

    transaction_list = await transaction_service.get_transaction_list(
        user, account_id, date_start, date_end
    )
    # Sort the transactions by date.
    transaction_list.sort(key=lambda x: x.information.date, reverse=True)

    # Group the transactions by date.
    transaction_list_grouped = [
        {"date": date, "transactions": list(transactions)}
        for date, transactions in groupby(
            transaction_list, key=lambda x: x.information.date
        )
    ]
    return render_dashboard_template(
        "pages/dashboard/page_single_account.html",
        request,
        {"account": account, "transaction_list_grouped": transaction_list_grouped},
    )


@router.get("/{account_id}/edit")
async def page_update_account_form(
    request: Request, account_id: int, user: models.User = Depends(current_active_user)
):
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    form = schemas.CreateAccountForm(request, data=account.__dict__)

    return render_dashboard_template(
        "pages/dashboard/page_update_account.html",
        request,
        {"account_id": account_id, "form": form},
    )


@csrf_protect
@router.post("/{account_id}/edit")
async def page_update_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
):
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    form = await schemas.CreateAccountForm.from_formdata(request)

    if not await form.validate_on_submit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Validation error"
        )

    account = schemas.Account(**form.data)

    response = await tm.transaction(service.update_account, user, account_id, account)

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )


@csrf_protect
@router.get("/{account_id}/add-transaction")
async def page_create_transaction_form(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
):
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    category_list = await category_service.get_categories(user)
    form = schemas.CreateTransactionForm(request)
    form.category_id.choices = group_categories_by_section(category_list)

    return render_dashboard_template(
        "pages/dashboard/page_create_transaction.html",
        request,
        {"form": form, "account_id": account_id},
    )


@router.get("/{account_id}/transactions/{transaction_id}")
async def page_update_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_user),
):
    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form = schemas.CreateTransactionForm(request, data=transaction.information.__dict__)
    category_list = await category_service.get_categories(user)
    form.category_id.choices = group_categories_by_section(category_list)
    form.date.data = transaction.information.date.strftime("%Y-%m-%d")

    return render_dashboard_template(
        "pages/dashboard/page_update_transaction.html",
        request,
        {"transaction": transaction, "account_id": account_id, "form": form},
    )


@router.post("/{account_id}/transactions/{transaction_id}")
async def page_update_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_user),
):
    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form = await schemas.CreateTransactionForm.from_formdata(request)
    category_list = await category_service.get_categories(user)
    form.category_id.choices = group_categories_by_section(category_list)

    if not await form.validate_on_submit():
        return render_dashboard_template(
            "pages/dashboard/page_update_transaction.html",
            request,
            {"form": form, "account_id": account_id, "transaction": transaction},
        )

    transaction_information = schemas.TransactionInformtionUpdate(
        account_id=account_id, **form.data
    )

    response = await tm.transaction(
        transaction_service.update_transaction,
        user,
        transaction_id,
        transaction_information,
    )

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )


@router.post("/{account_id}/add-transaction")
async def page_create_transaction(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
):
    category_list = await category_service.get_categories(user)
    form = await schemas.CreateTransactionForm.from_formdata(request)
    form.category_id.choices = group_categories_by_section(category_list)

    if not await form.validate_on_submit():
        return render_dashboard_template(
            "pages/dashboard/page_create_transaction.html",
            request,
            {"form": form, "account_id": account_id},
        )

    transaction = schemas.TransactionInformationCreate(
        account_id=account_id, **form.data
    )

    response = await tm.transaction(
        transaction_service.create_transaction, user, transaction
    )

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )
