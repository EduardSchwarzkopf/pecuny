from collections import defaultdict
from typing import List, Optional, Type, Union

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette_wtf import StarletteForm

from app import models, schemas, templates
from app.services.category import CategoryService
from app.services.frequency import FrequencyService
from app.services.wallets import WalletService
from app.utils.dataclasses_utils import FinancialSummary
from app.utils.enums import FeedbackType


def set_feedback(
    request: Request,
    feedback_type: FeedbackType,
    feedback_message: str,
):
    """Set the feedback type and message in the request state.

    Args:
        request: The request object.
        feedback_type: The type of feedback.
        feedback_message: The feedback message.

    Returns:
        None

    Raises:
        None
    """
    request.state.feedback_type = feedback_type.value
    request.state.feedback_message = feedback_message


def get_default_context(request: Request) -> dict:
    """Get the default context for a request.

    Args:
        request: The request object.

    Returns:
        dict: The default context dictionary.

    Raises:
        None
    """
    return {
        "request": request,
        "breadcrumbs": request.state.breadcrumb_builder.build(),
        "header_links": getattr(request.state, "header_links", None),
        "feedback_type": getattr(request.state, "feedback_type", None),
        "feedback_message": getattr(request.state, "feedback_message", None),
    }


def render_template(
    template: str, request: Request, context_extra: Optional[dict] = None
) -> HTMLResponse:
    """Render a template with the provided context.

    Args:
        template: The name of the template to render.
        request: The request object.
        context_extra: Optional extra context to include.

    Returns:
        TemplateResponse: The rendered template response.

    Raises:
        None
    """
    context = get_default_context(request)

    if context_extra is None:
        context_extra = {}

    return templates.TemplateResponse(request, template, {**context, **context_extra})


def render_form_template(template: str, request: Request, form: StarletteForm):
    """Render a template with a form included in the context.

    Args:
        template: The name of the template to render.
        request: The request object.
        form: The form object to include in the context.

    Returns:
        TemplateResponse: The rendered template response.

    Raises:
        None
    """
    return render_template(template, request, {"form": form})


def render_transaction_form_template(
    request: Request,
    form: StarletteForm,
    wallet_id: int,
    page_name: str,
    transaction: Optional[models.Transaction] = None,
) -> HTMLResponse:
    """
    Renders a transaction form template for display.

    Args:
        request: The request object.
        form: The form to render.
        wallet_id: The ID of the wallet.
        page_name: The name of the page.

    Returns:
        The rendered transaction form template.
    """

    url_params = {"transaction_id": transaction.id} if transaction else {}
    return render_template(
        "pages/dashboard/page_form_transaction.html",
        request,
        {
            "form": form,
            "wallet_id": wallet_id,
            "transaction": transaction,
            "action_url": request.url_for(page_name, wallet_id=wallet_id, **url_params),
        },
    )


def group_categories_by_section(categorie_list: list[schemas.CategoryData]):
    """Group categories by section.

    Args:
        categorie_list: A list of category data.

    Returns:
        dict:
            A dictionary where the keys are section labels and
            the values are lists of category IDs and labels.

    Raises:
        None
    """
    grouped_data = defaultdict(list)
    for item in categorie_list:
        grouped_data[item.section.label].append((item.id, item.label))
    return grouped_data


def add_breadcrumb(request: Request, label: str, url: Union[str, None]):
    """Add a breadcrumb to the request state.

    Args:
        request: The request object.
        label: The label of the breadcrumb.
        url: The URL of the breadcrumb.

    Returns:
        None

    Raises:
        None
    """
    request.state.breadcrumb_builder.add(label, url)


def calculate_financial_summary(
    transaction_list: List[Union[models.Transaction, models.TransactionScheduled]],
) -> FinancialSummary:
    """
    Calculates the financial summary based on a list of transactions.

    Args:
        transaction_list: A list of transactions to calculate the summary.

    Returns:
        A FinancialSummary object containing total expenses, total income, and overall total.
    """
    summary = FinancialSummary()

    for transaction in transaction_list:

        if transaction.information.amount < 0:
            summary.expenses += transaction.information.amount
            continue

        summary.income += transaction.information.amount

    return summary


async def populate_transaction_form_wallet_choices(
    wallet_id: int,
    user: models.User,
    form: Type[
        Union[
            schemas.CreateScheduledTransactionForm,
            schemas.UpdateScheduledTransactionForm,
            schemas.UpdateTransactionForm,
            schemas.CreateTransactionForm,
        ]
    ],
    first_select_label,
) -> None:
    """
    Populates the wallet choices in the transaction form.

    Args:
        wallet_id: The ID of the wallet.
        user: The current active user.
        form: The create transaction form.
        first_select_label: The label for the first select option.

    Returns:
        None
    """
    service = WalletService()
    wallet_list = await service.get_wallets(user)

    if wallet_list is None:
        return None

    wallet_list_length = len(wallet_list)

    wallet_choices = (
        [(0, first_select_label)]
        + [
            (wallet.id, wallet.label)
            for wallet in wallet_list
            if wallet is not None and wallet.id != wallet_id
        ]
        if wallet_list_length > 1
        else [(0, "No other wallets found")]
    )

    form.offset_wallet_id.choices = wallet_choices
    if wallet_list_length == 1:
        form.offset_wallet_id.data = 0


async def populate_transaction_form_category_choices(
    user: models.User,
    form: Type[
        Union[
            schemas.CreateScheduledTransactionForm,
            schemas.UpdateScheduledTransactionForm,
            schemas.UpdateTransactionForm,
            schemas.CreateTransactionForm,
        ]
    ],
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
    wallet_id: int,
    user: models.User,
    form: Type[
        Union[
            schemas.CreateScheduledTransactionForm,
            schemas.UpdateScheduledTransactionForm,
            schemas.UpdateTransactionForm,
            schemas.CreateTransactionForm,
        ]
    ],
    first_select_label: str = "Select target wallet for transfers",
) -> None:
    """
    Populates the choices in the transaction form.

    Args:
        wallet_id: The ID of the wallet.
        user: The current active user.
        form: The create transaction form.
        first_select_label: The label for the first select option.

    Returns:
        None
    """

    await populate_transaction_form_category_choices(user, form)

    if isinstance(
        form,
        (
            schemas.CreateScheduledTransactionForm,
            schemas.UpdateScheduledTransactionForm,
        ),
    ):
        await populate_transaction_form_frequency_choices(form)

    await populate_transaction_form_wallet_choices(
        wallet_id, user, form, first_select_label
    )
