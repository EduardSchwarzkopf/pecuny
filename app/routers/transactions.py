from fastapi import Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette_wtf import csrf_protect
from app.config import settings
from fastapi.exceptions import HTTPException
from starlette import status
from app.utils import PageRouter
from app.utils.template_utils import (
    group_categories_by_section,
    render_template,
)
from app import schemas, transaction_manager as tm, models
from app.services import (
    accounts as service,
    transactions as transaction_service,
    categories as category_service,
)
from app.auth_manager import current_active_user
from app.routers.accounts import (
    handle_account_route,
    router as account_router,
    handle_account_route,
)

PREFIX = account_router.prefix + "/{account_id}/transactions"

router = PageRouter(prefix=PREFIX, tags=["Transactions"])


async def populate_transaction_form_choices(
    account_id: int,
    user: models.User,
    form: schemas.CreateTransactionForm,
    first_select_label: str = "Select target account for transfers",
) -> None:
    await populate_transaction_form_category_choices(user, form)
    await populate_transaction_form_account_choices(
        account_id, user, form, first_select_label
    )


async def populate_transaction_form_account_choices(
    account_id: int,
    user: models.User,
    form: schemas.CreateTransactionForm,
    first_select_label,
) -> None:
    account_list = await service.get_accounts(user)
    account_list_length = len(account_list)

    account_choices = [(0, "No other accounts found")]
    if account_list_length == 1:
        form.offset_account_id.data = 0

    if account_list_length > 1:
        account_choices = [
            (account.id, account.label)
            for account in account_list
            if account.id != account_id
        ]
        account_choices.insert(
            0,
            (0, first_select_label),
        )

    form.offset_account_id.choices = account_choices


async def populate_transaction_form_category_choices(
    user: models.User, form: schemas.CreateTransactionForm
) -> None:
    category_list = category_service.get_categories(user)
    form.category_id.choices = group_categories_by_section(await category_list)


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


@csrf_protect
@router.get("/add-income/")
async def page_create_income_form(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_user),
):
    await handle_account_route(request, user, account_id)

    form = schemas.CreateTransactionForm(request)
    await populate_transaction_form_choices(account_id, user, form)

    is_income = True

    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "account_id": account_id,
            "is_income": is_income,
            "action_url": request.url_for(
                "page_create_transaction", account_id=account_id
            ).include_query_params(is_income=is_income),
        },
    )


@csrf_protect
@router.get("/add-expense/")
async def page_create_expense_form(
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
            "is_income": False,
            "action_url": router.url_path_for(
                "page_create_transaction", account_id=account_id
            ),
        },
    )


@router.post("/add-transaction")
async def page_create_transaction(
    request: Request,
    account_id: int,
    is_income: bool = False,
    user: models.User = Depends(current_active_user),
):
    await handle_account_route(request, user, account_id)

    form = await schemas.CreateTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(account_id, user, form)

    form.amount.data = abs(form.amount.data)

    if is_income is False:
        form.amount.data *= -1

    if not await form.validate_on_submit():
        return render_template(
            "pages/dashboard/page_form_transaction.html",
            request,
            {
                "form": form,
                "account_id": account_id,
                "is_income": is_income,
                "action_url": router.url_path_for(
                    "page_create_transaction", account_id=account_id
                ),
            },
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
        account_router.url_path_for("page_get_account", account_id=account_id),
        status_code=302,
    )


@router.get("/{transaction_id}")
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
    await populate_transaction_form_choices(
        account_id, user, form, "Linked account (not editable)"
    )
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


@router.post("/{transaction_id}")
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
    await populate_transaction_form_choices(
        account_id, user, form, "Linked account (not editable)"
    )

    if not await form.validate_on_submit():
        form.date.data = transaction.information.date.strftime("%Y-%m-%d")
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
        account_router.url_path_for("page_get_account", account_id=account_id),
        status_code=302,
    )


@csrf_protect
@router.post("/{transaction_id}/delete")
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
        account_router.url_path_for("page_get_account", account_id=account_id),
        status_code=302,
    )
