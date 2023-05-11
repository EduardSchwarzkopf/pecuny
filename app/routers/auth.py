from app import templates

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

router = APIRouter()
template_prefix = "pages/auth"


@router.get(
    path="/login", tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_login(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(f"{template_prefix}/login.html", context)


@router.get(
    path="/register", tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_regsiter(
    request: Request,
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(f"{template_prefix}/register.html", context)


@router.get(
    path="/forgot-password",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def get_forgot_password(
    request: Request,
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(
        f"{template_prefix}/forgot-password.html", context
    )


@router.get(
    path="/reset-password",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def get_reset_password(
    request: Request,
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(f"{template_prefix}/reset-password.html", context)
