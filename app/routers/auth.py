from app import templates

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.models import User
from fastapi.security import OAuth2PasswordRequestForm
from app.services import users as service
from app import transaction_manager as tm

from app.auth_manager import (
    fastapi_users,
    get_user_manager,
    auth_backend,
    UserManager,
    JWTStrategy,
)
from fastapi_users.exceptions import UserNotExists

current_active_user = fastapi_users.current_user(optional=True)

router = APIRouter()
template_prefix = "pages/auth"


@router.get(
    path="/login/", tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_login(request: Request, user: User = Depends(current_active_user)):
    print(user)
    if user:
        return RedirectResponse("/")

    context = {"request": request}
    return templates.TemplateResponse(f"{template_prefix}/login.html", context)


@router.post(
    "/login/",
    response_class=RedirectResponse,
)
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    strategy: JWTStrategy = Depends(auth_backend.get_strategy),
):
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        return RedirectResponse("/login?credentials=False", status_code=302)

    if not user.is_verified:
        return RedirectResponse("/login?verified=False", status_code=302)

    response = await auth_backend.login(strategy, user)
    await user_manager.on_after_login(user, request, response)
    return response


@router.get(
    path="/register/", tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_regsiter(
    request: Request,
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(f"{template_prefix}/register.html", context)


@router.post("/register/", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    displayname: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        existing_user = await user_manager.get_by_email(email)
    except UserNotExists:
        existing_user = None

    context = {"request": request}
    if existing_user is not None:
        context["error"] = "Email already in use"
        return templates.TemplateResponse(f"{template_prefix}/register.html", context)

    if password != password_confirm:
        context["error"] = "Passwords do not match"
        return templates.TemplateResponse(f"{template_prefix}/register.html", context)

    result = await service.create_user(user_manager, email, displayname, password)
    return templates.TemplateResponse(f"{template_prefix}/login.html", context)


@router.get(
    path="/verify",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def verify_email(
    request: Request,
    token: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    status = await service.verify_email(user_manager, token)
    return templates.TemplateResponse(
        f"{template_prefix}/email-verify.html",
        {"request": request, "verification_status": status},
    )


@router.get(
    path="/forgot-password/",
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
    path="/reset-password/",
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
