from typing import Optional, Dict
from fastapi import Request
from app import templates


def get_default_context(request: Request, feedback: Optional[Dict[str, str]] = None):
    context = {
        "request": request,
        "header_links": request.state.header_links,
    }

    if feedback:
        context["feedback_type"] = feedback["type"]
        context["feedback_message"] = feedback["message"]

    return context


def render_template(
    template: str, request: Request, feedback: Optional[Dict[str, str]] = None
):
    return templates.TemplateResponse(template, get_default_context(request, feedback))
