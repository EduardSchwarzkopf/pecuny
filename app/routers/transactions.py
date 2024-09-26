from fastapi import Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette_wtf import csrf_protect

from app import models, schemas
from app.auth_manager import current_active_verified_user
from app.routers.wallets import handle_wallet_route
from app.routers.wallets import router as wallet_router
from app.services.transactions import TransactionService
from app.utils import PageRouter
from app.utils.template_utils import (
    populate_transaction_form_choices,
    render_transaction_form_template,
)
from app.utils.wallet_utils import get_wallet_list_template

PREFIX = wallet_router.prefix + "/{wallet_id}/transactions"

router = PageRouter(prefix=PREFIX, tags=["Transactions"])

# pylint: disable=duplicate-code


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


@csrf_protect
@router.get("/add")
async def page_create_transaction_form(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
):
    """
    Renders the create transaction form page.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered create transaction
    """
    await handle_wallet_route(request, user, wallet_id)

    form = schemas.CreateTransactionForm(request)
    await populate_transaction_form_choices(wallet_id, user, form)

    return render_transaction_form_template(
        request, form, wallet_id, "page_create_transaction"
    )


@router.post("/add")
async def page_create_transaction(
    request: Request,
    wallet_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Handles the creation of a transaction.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the wallet page.
    """

    await handle_wallet_route(request, user, wallet_id)

    form = await schemas.CreateTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(wallet_id, user, form)

    if not await form.validate_on_submit():
        return render_transaction_form_template(
            request, form, wallet_id, "page_create_transaction"
        )

    if form.is_expense.data:
        form.amount.data *= -1

    transaction = schemas.TransactionData(wallet_id=wallet_id, **form.data)

    await transaction_service.create_transaction(user, transaction)

    return RedirectResponse(
        wallet_router.url_path_for("page_get_wallet", wallet_id=wallet_id),
        status_code=302,
    )


@router.get("/{transaction_id}")
async def page_update_transaction_get(
    request: Request,
    wallet_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Renders the transaction update form page.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered transaction update form page.
    """

    await handle_wallet_route(request, user, wallet_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    form: schemas.UpdateTransactionForm = schemas.UpdateTransactionForm(
        request, data=transaction.information.__dict__
    )
    await populate_transaction_form_choices(
        wallet_id, user, form, "Linked wallet (not editable)"
    )
    form.date.data = transaction.information.date.strftime("%Y-%m-%d")

    form_amount = form.amount.data
    if form_amount < 0:
        form.is_expense.data = True

    form.amount.data = abs(form_amount)

    if transaction.offset_transactions_id:
        offset_transaction = await transaction_service.get_transaction(
            user, transaction.offset_transactions_id
        )

        if offset_transaction is not None:
            form.offset_wallet_id.data = offset_transaction.wallet_id
    return render_transaction_form_template(
        request,
        form,
        wallet_id,
        "page_update_transaction_get",
        transaction,
    )


@router.post("/{transaction_id}")
async def page_update_transaction_post(
    request: Request,
    wallet_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Handles the update of a transaction.

    Args:
        request: The request object.
        wallet_id: The ID of the wallet.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered transaction update form page or a redirect response.
    """

    await handle_wallet_route(request, user, wallet_id)

    transaction = await transaction_service.get_transaction(user, transaction_id)

    form = await schemas.UpdateTransactionForm.from_formdata(request)
    await populate_transaction_form_choices(
        wallet_id, user, form, "Linked wallet (not editable)"
    )

    if not await form.validate_on_submit():
        form.date.data = transaction.information.date.strftime("%Y-%m-%d")
        return render_transaction_form_template(
            request,
            form,
            wallet_id,
            "page_update_transaction_get",
            transaction,
        )

    if form.is_expense.data:
        form.amount.data *= -1

    transaction_information = schemas.TransactionInformtionUpdate(
        wallet_id=wallet_id, **form.data
    )

    await transaction_service.update_transaction(
        user, transaction_id, transaction_information
    )

    return RedirectResponse(
        wallet_router.url_path_for("page_get_wallet", wallet_id=wallet_id),
        status_code=302,
    )


@csrf_protect
@router.post("/{transaction_id}/delete")
async def page_delete_transaction(
    wallet_id: int,
    transaction_id: int,
    user: models.User = Depends(current_active_verified_user),
    transaction_service: TransactionService = Depends(TransactionService.get_instance),
):
    """
    Handles the deletion of a transaction.

    Args:
        wallet_id: The ID of the wallet.
        transaction_id: The ID of the transaction.
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the wallet page.
    """

    transaction = await transaction_service.get_transaction(user, transaction_id)

    await transaction_service.delete_transaction(user, transaction_id)

    return RedirectResponse(
        wallet_router.url_path_for("page_get_wallet", wallet_id=wallet_id),
        status_code=302,
    )
