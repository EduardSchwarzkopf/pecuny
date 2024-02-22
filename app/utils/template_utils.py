from fastapi import Request
from starlette_wtf import StarletteForm
from app import templates, schemas
from app.utils.enums import FeedbackType
from typing import Optional, List
from collections import defaultdict


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
    template: str, request: Request, context_extra: Optional[dict] = {}
):  # sourcery skip: default-mutable-arg
    context = get_default_context(request)
    return templates.TemplateResponse(template, {**context, **context_extra})


def render_form_template(template: str, request: Request, form: StarletteForm):
    return render_template(template, request, {"form": form})


def group_categories_by_section(categorie_list: List[schemas.CategoryData]):
    grouped_data = defaultdict(list)
    for item in categorie_list:
        grouped_data[item.section.label].append((item.id, item.label))
    return grouped_data


def add_breadcrumb(request: Request, label: str, url: str):
    request.state.breadcrumb_builder.add(label, url)
