from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette_wtf import csrf_protect

from app import models, schemas
from app import transaction_manager as tm
from app.auth_manager import current_active_verified_user
from app.routers.accounts import handle_account_route
from app.routers.accounts import router as account_router
from app.services.accounts import AccountService
from app.services.categories import CategoryService
from app.services.frequency import FrequencyService
from app.services.scheduled_transactions import ScheduledTransactionService
from app.utils import PageRouter
from app.utils.template_utils import (
    add_breadcrumb,
    group_categories_by_section,
    render_template,
)

PREFIX = account_router.prefix + "/{account_id}/scheduled-transactions"

router = PageRouter(prefix=PREFIX, tags=["Scheduled Transactions"])


async def populate_transaction_form_account_choices(
    account_id: int,
    user: models.User,
    form: schemas.CreateScheduledTransactionForm,
    first_select_label,
) -> None:
    """
    Populates the account choices in the transaction form.

    Args:
        account_id: The ID of the account.
        user: The current active user.
        form: The create transaction form.
        first_select_label: The label for the first select option.

    Returns:
        None
    """
    service = AccountService()
    account_list = await service.get_accounts(user)

    if account_list is None:
        return None

    account_list_length = len(account_list)

    account_choices = (
        [(0, first_select_label)]
        + [
            (account.id, account.label)
            for account in account_list
            if account.id != account_id
        ]
        if account_list_length > 1
        else [(0, "No other accounts found")]
    )

    form.offset_account_id.choices = account_choices
    if account_list_length == 1:
        form.offset_account_id.data = 0


async def populate_transaction_form_category_choices(
    user: models.User, form: schemas.CreateScheduledTransactionForm
) -> None:
    """
    Populates the category choices in the transaction form.

    Args:
        user: The current active user.
        form: The create transaction form.

    Returns:
        None
    """
    category_service = CategoryService()
    category_list = await category_service.get_categories(user) or []
    category_data_list = [
        schemas.CategoryData(**category.__dict__) for category in category_list
    ]
    form.category_id.choices = group_categories_by_section(category_data_list)


async def populate_transaction_form_frequency_choices(
    form: schemas.CreateScheduledTransactionForm,
) -> None:
    """
    Populates the frequency choices in the transaction form.

    Args:
        user: The current active user.
        form: The create transaction form.

    Returns:
        None
    """
    service = FrequencyService()
    frequency_list = await service.get_frequency_list() or []

    choices = [(frequency.id, frequency.label) for frequency in frequency_list]

    form.frequency_id.choices = choices


async def populate_transaction_form_choices(
    account_id: int,
    user: models.User,
    form: schemas.CreateScheduledTransactionForm,
    first_select_label: str = "Select target account for transfers",
) -> None:
    """
    Populates the choices in the transaction form.

    Args:
        account_id: The ID of the account.
        user: The current active user.
        form: The create transaction form.
        first_select_label: The label for the first select option.

    Returns:
        None
    """

    await populate_transaction_form_category_choices(user, form)
    await populate_transaction_form_frequency_choices(form)
    await populate_transaction_form_account_choices(
        account_id, user, form, first_select_label
    )


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

    add_breadcrumb(request, "Scheduled Transactions", None)

    expenses = 0
    income = 0
    total = 0

    for transaction in transaction_list:
        if transaction.information.amount < 0:
            expenses += transaction.information.amount
        else:
            income += transaction.information.amount

        total += transaction.information.amount

    return render_template(
        "pages/dashboard/page_scheduled_transactions.html",
        request,
        {
            "account": account,
            "scheduled_transaction_list": transaction_list,
            "expenses": expenses,
            "income": income,
            "total": total,
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

    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "account_id": account_id,
            "action_url": request.url_for(
                "page_create_transaction", account_id=account_id
            ),
        },
    )


@router.post("/add")
async def page_create_transaction(
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

    if form.is_expense.data:
        form.amount.data *= -1

    transaction = schemas.TransactionData(account_id=account_id, **form.data)

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
    await populate_transaction_form_choices(
        account_id, user, form, "Linked account (not editable)"
    )
    form.date_start.data = transaction.information.date.strftime("%Y-%m-%d")
    form.date_end.data = transaction.information.date.strftime("%Y-%m-%d")

    form_amount = form.amount.data
    if form_amount < 0:
        form.is_expense.data = True

    form.amount.data = abs(form_amount)
    form.frequency_id.data = transaction.frequency_id

    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "account_id": account_id,
            "transaction_id": transaction.id,
            "action_url": router.url_path_for(
                "page_update_scheduled_transaction_get",
                account_id=account_id,
                transaction_id=transaction.id,
            ),
        },
    )


@router.post("/{transaction_id}")
async def page_update_transaction_post(
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
                    "page_update_scheduled_transaction_get",
                    account_id=account_id,
                    transaction_id=transaction.id,
                ),
            },
        )

    if form.is_expense.data:
        form.amount.data *= -1

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

    response = await tm.transaction(
        transaction_service.delete_transaction, user, transaction_id
    )

    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kaputt")

    return RedirectResponse(
        account_router.url_path_for("page_get_account", account_id=account_id),
        status_code=302,
    )
