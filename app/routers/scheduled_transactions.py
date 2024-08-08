from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette_wtf import csrf_protect

from app import models, schemas
from app import transaction_manager as tm
from app.auth_manager import current_active_verified_user
from app.date_manager import now
from app.routers.accounts import handle_account_route
from app.routers.accounts import router as account_router
from app.services.scheduled_transactions import ScheduledTransactionService
from app.utils import PageRouter
from app.utils.template_utils import (
    add_breadcrumb,
    calculate_financial_summary,
    populate_transaction_form_choices,
    render_template,
    render_transaction_form_template,
)

PREFIX = account_router.prefix + "/{account_id}/scheduled-transactions"

router = PageRouter(prefix=PREFIX, tags=["Scheduled Transactions"])

# pylint: disable=duplicate-code


@router.get("/", response_class=HTMLResponse)
async def page_list_scheduled_transactions(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
    service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Renders the list accounts page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered list accounts page.
    """

    transaction_list = await service.get_transaction_list(user, account_id)
    account = await handle_account_route(request, user, account_id)

    add_breadcrumb(request, "Scheduled Transactions", "")

    financial_summary = calculate_financial_summary(transaction_list)
    expenses = financial_summary.expenses
    income = financial_summary.income
    total = financial_summary.total

    return render_template(
        "pages/dashboard/page_scheduled_transactions.html",
        request,
        {
            "account": account,
            "scheduled_transaction_list": transaction_list,
            "expenses": expenses,
            "income": income,
            "total": total,
            "now": now(),
        },
    )


@csrf_protect
@router.get("/add")
async def page_create_scheduled_transaction_form(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the create transaction form page.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered create transaction
    """
    await handle_account_route(request, user, account_id)
    add_breadcrumb(
        request,
        "Scheduled Transactions",
        url=request.url_for("page_list_scheduled_transactions", account_id=account_id),
    )

    form = schemas.CreateScheduledTransactionForm(request)
    await populate_transaction_form_choices(account_id, user, form)

    return render_transaction_form_template(
        request, form, account_id, "page_create_scheduled_transaction"
    )


@router.post("/add")
async def page_create_scheduled_transaction(
    request: Request,
    account_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Handles the creation of a transaction.

    Args:
        request: The request object.
        account_id: The ID of the account.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the account page.
    """

    await handle_account_route(request, user, account_id)

    form = await schemas.CreateScheduledTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(account_id, user, form)

    if not await form.validate_on_submit():
        return render_transaction_form_template(
            request, form, account_id, "page_create_scheduled_transaction"
        )

    if form.is_expense.data:
        form.amount.data *= -1

    transaction = schemas.ScheduledTransactionInformationCreate(
        account_id=account_id, **form.data
    )

    response = await tm.transaction(
        transaction_service.create_scheduled_transaction, user, transaction
    )

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        request.url_for("page_list_scheduled_transactions", account_id=account_id),
        status_code=302,
    )


@router.get("/{transaction_id}")
async def page_update_scheduled_transaction_get(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Renders the transaction update form page.

    Args:
        request: The request object.
        account_id: The ID of the account.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered transaction update form page.
    """

    await handle_account_route(request, user, account_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form: schemas.UpdateScheduledTransactionForm = (
        schemas.UpdateScheduledTransactionForm(
            request, data=transaction.information.__dict__
        )
    )
    await populate_transaction_form_choices(account_id, user, form)
    form.date_start.data = transaction.information.date.strftime("%Y-%m-%d")
    form.date_end.data = transaction.information.date.strftime("%Y-%m-%d")

    form_amount = form.amount.data
    if form_amount < 0:
        form.is_expense.data = True

    form.amount.data = abs(form_amount)
    form.frequency_id.data = transaction.frequency_id

    add_breadcrumb(
        request,
        "Scheduled Transactions",
        url=request.url_for("page_list_scheduled_transactions", account_id=account_id),
    )

    return render_transaction_form_template(
        request,
        form,
        account_id,
        "page_update_scheduled_transaction_get",
        transaction,
    )


@router.post("/{transaction_id}")
async def page_update_scheduled_transaction_post(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Handles the update of a transaction.

    Args:
        request: The request object.
        account_id: The ID of the account.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered transaction update form page or a redirect response.
    """

    await handle_account_route(request, user, account_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    form = await schemas.UpdateScheduledTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(account_id, user, form)

    if not await form.validate_on_submit():
        form.date.data = transaction.information.date.strftime("%Y-%m-%d")
        return render_transaction_form_template(
            request,
            form,
            account_id,
            "page_update_scheduled_transaction_get",
            transaction,
        )

    if form.is_expense.data:
        form.amount.data *= -1

    transaction_information = schemas.ScheduledTransactionInformtionUpdate(
        account_id=account_id, **form.data
    )

    await tm.transaction(
        transaction_service.update_scheduled_transaction,
        user,
        transaction_id,
        transaction_information,
    )

    return RedirectResponse(
        request.url_for("page_list_scheduled_transactions", account_id=account_id),
        status_code=302,
    )


@csrf_protect
@router.post("/{transaction_id}/delete")
async def page_delete_scheduled_transaction(
    request: Request,
    account_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: ScheduledTransactionService = Depends(
        ScheduledTransactionService.get_instance
    ),
):
    """
    Handles the deletion of a transaction.

    Args:
        account_id: The ID of the account.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the account page.
    """

    transaction = await transaction_service.get_transaction(user, transaction_id)

    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    await tm.transaction(
        transaction_service.delete_scheduled_transaction, user, transaction_id
    )

    return RedirectResponse(
        request.url_for("page_list_scheduled_transactions", account_id=account_id),
        status_code=302,
    )
