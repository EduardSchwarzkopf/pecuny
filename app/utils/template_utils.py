from collections import defaultdict
from typing import Optional, Union

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette_wtf import StarletteForm

from app import schemas, templates
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

    return templates.TemplateResponse(template, {**context, **context_extra})


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
    account_id: int,
    page_name: str,
    transaction: Optional[models.Transaction] = None,
) -> HTMLResponse:
    """
    Renders a transaction form template for display.

    Args:
        request: The request object.
        form: The form to render.
        account_id: The ID of the account.
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
            "account_id": account_id,
            "transaction": transaction,
            "action_url": request.url_for(
                page_name, account_id=account_id, **url_params
            ),
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
