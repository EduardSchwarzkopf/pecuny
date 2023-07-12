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
    add_breadcrumb,
    group_categories_by_section,
    render_template,
    set_feedback,
)
from app import schemas, transaction_manager as tm, models
from app.services import (
    accounts as service,
    transactions as transaction_service,
    categories as category_service,
)
from app.auth_manager import current_active_user
from app.routers.dashboard import router as dashboard_router

PREFIX = f"{dashboard_router.prefix}/accounts"
router = PageRouter(prefix=PREFIX, tags=["Accounts"])


async def handle_account_route(
    request, user: models.User, account_id: int, create_link=True
) -> models.Account:
    account = await service.get_account(user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    add_breadcrumb(request, "Accounts", PREFIX)
    account_url = f"{PREFIX}/{account_id}" if create_link else ""
    add_breadcrumb(request, account.label, account_url)

    return account


async def populate_transaction_form_choices(
    account_id: int, user: models.User, form: schemas.CreateTransactionForm
) -> None:
    category_list = category_service.get_categories(user)
    account_list = service.get_accounts(user)
    form.category_id.choices = group_categories_by_section(await category_list)

    account_choices = [
        (account.id, account.label)
        for account in await account_list
        if account.id != account_id
    ]
    account_choices.insert(0, (0, "---"))
    form.offset_account_id.choices = account_choices


@router.get("/", response_class=HTMLResponse)
async def page_list_accounts(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    account_list = await service.get_accounts(user)
    total_balance = sum(account.balance for account in account_list)

    return render_template(
        "pages/dashboard/page_list_accounts.html",
        request,
        {
            "account_list": account_list,
            "max_allowed_accounts": settings.max_allowed_accounts,
            "total_balance": total_balance,
        },
    )


async def max_accounts_reached(user: models.User, request: Request) -> RedirectResponse:
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
    user: models.User = Depends(current_active_user),
):
    if response := await max_accounts_reached(user, request):
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
    request: Request, user: models.User = Depends(current_active_user)
):
    if response := await max_accounts_reached(user, request):
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

    return RedirectResponse(router.url_path_for("page_list_accounts"), status_code=302)


@router.get("/{account_id}")
async def page_get_account(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
    date_start: datetime = Cookie(None),
    date_end: datetime = Cookie(None),
):
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

    transaction_list = await transaction_service.get_transaction_list(
        user, account_id, date_start, date_end
    )

    expenses = 0
    income = 0
    total = 0

    for transaction in transaction_list:
        if transaction.information.amount < 0:
            expenses += transaction.information.amount
        else:
            income += transaction.information.amount

        total += transaction.information.amount

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
    request: Request, account_id: int, user: models.User = Depends(current_active_user)
):
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
    user: models.User = Depends(current_active_user),
):
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
    user: models.User = Depends(current_active_user),
):
    account = await handle_account_route(request, user, account_id)

    form = await schemas.UpdateAccountForm.from_formdata(request)

    if not await form.validate_on_submit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Validation error"
        )

    account = schemas.Account(**form.data, balance=account.balance)

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
    await handle_account_route(request, user, account_id)

    form = schemas.CreateTransactionForm(request)
    await populate_transaction_form_choices(account_id, user, form)

    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "account_id": account_id,
            "action_url": router.url_path_for(
                "page_create_transaction", account_id=account_id
            ),
        },
    )


@router.get("/{account_id}/transactions/{transaction_id}")
async def page_update_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_user),
):
    await handle_account_route(request, user, account_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form = schemas.UpdateTransactionForm(request, data=transaction.information.__dict__)
    await populate_transaction_form_choices(account_id, user, form)
    form.date.data = transaction.information.date.strftime("%Y-%m-%d")

    if transaction.offset_transactions_id:
        offset_transaction = await transaction_service.get_transaction(
            user, transaction.offset_transactions_id
        )
        form.offset_account_id.data = offset_transaction.account_id

    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "account_id": account_id,
            "transaction_id": transaction.id,
            "action_url": router.url_path_for(
                "page_update_transaction",
                account_id=account_id,
                transaction_id=transaction.id,
            ),
        },
    )


@router.post("/{account_id}/transactions/{transaction_id}")
async def page_update_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_user),
):
    await handle_account_route(request, user, account_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form = await schemas.UpdateTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(account_id, user, form)

    if not await form.validate_on_submit():
        return render_template(
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
    await handle_account_route(request, user, account_id)

    form = await schemas.CreateTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(account_id, user, form)

    if not await form.validate_on_submit():
        return render_template(
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


@csrf_protect
@router.post("/{account_id}/transactions/{transaction_id}/delete")
async def page_delete_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_user),
):
    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    response = await tm.transaction(
        transaction_service.delete_transaction, user, transaction_id
    )

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        router.url_path_for("page_get_account", account_id=account_id), status_code=302
    )
