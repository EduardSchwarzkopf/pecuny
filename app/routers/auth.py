from app import templates

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.models import User
from fastapi.security import OAuth2PasswordRequestForm
from app.routers.api.users import (
    fastapi_users,
    get_user_manager,
    auth_backend,
    UserManager,
    JWTStrategy,
)

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
