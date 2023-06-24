from datetime import datetime
import calendar
from itertools import groupby
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette_wtf import csrf_protect
from app.config import settings
from fastapi.exceptions import HTTPException
from starlette import status
from app.utils import PageRouter
from app.utils.template_utils import render_template
from app import schemas, transaction_manager as tm, models
from app.services import accounts as service, transactions as transaction_service
from app.auth_manager import current_active_user

router = PageRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/", response_class=HTMLResponse)
async def page_accounts_list(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    account_list = await service.get_accounts(user)
    return render_template(
        "pages/dashboard/page_multiple_accounts.html",
        request,
        {
            "account_list": account_list,
            "max_allowed_accounts": settings.max_allowed_accounts,
        },
    )


def redirect_if_max_accounts(user):
    if service.check_max_accounts(user):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Maximum number of accounts reached",
        )


@csrf_protect
@router.get("/create-account", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    redirect_if_max_accounts(user)

    form = await schemas.CreateAccountForm.from_formdata(request)

    return render_template(
        "pages/dashboard/page_create_account.html", request, {"form": form}
    )


@csrf_protect
@router.post("/create-account")
async def page_create_account(
    request: Request, user: models.User = Depends(current_active_user)
):
    redirect_if_max_accounts(user)

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
    date_start: datetime = None,
    date_end: datetime = None,
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
    return render_template(
        "pages/dashboard/page_single_account.html",
        request,
        {"account": account, "transaction_list_grouped": transaction_list_grouped},
    )
