from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi_users import exceptions
from fastapi.security import OAuth2PasswordRequestForm

from app import templates
from app.auth_manager import UserManager, current_active_user, get_user_manager
from app.services.users import UserService
from app.models import User

from app.auth_manager import (
    get_user_manager,
    auth_backend,
    UserManager,
    JWTStrategy,
)

router = APIRouter()
template_prefix = "pages/auth"


async def get_user_service() -> UserService:
    return UserService()


@router.get(
    path="/login", tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_login(
    request: Request, user: User = Depends(current_active_user), error: str = ""
):
    if user:
        return RedirectResponse("/")

    context = {"request": request, "error": error}
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
        return RedirectResponse("/login?error=credentials", status_code=302)

    if not user.is_verified:
        return RedirectResponse("/login?error=verification", status_code=302)

    await auth_backend.login(strategy, user)
    return RedirectResponse("/")


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
    user_service: UserService = Depends(get_user_service),
):
    try:
        existing_user = await user_service.user_manager.get_by_email(email)
    except exceptions.UserNotExists:
        existing_user = None

    context = {"request": request}
    if existing_user is not None:
        context["feedback_type"] = "error"
        context["feedback_message"] = "Email already in use"
        return templates.TemplateResponse("fragments/feedback.html", context)

    if password != password_confirm:
        context["feedback_type"] = "error"
        context["feedback_message"] = "Passwords do not match"
        return templates.TemplateResponse("fragments/feedback.html", context)

    await user_service.create_user(email, displayname, password)
    return RedirectResponse("/login?success=register")


@router.get(
    path="/verify",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def verify_email(
    request: Request,
    token: str,
    user_service: UserService = Depends(get_user_service),
):
    status = await user_service.verify_email(token)
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


@router.post("/forgot-password/", response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    email: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    context = {"request": request}

    result = await user_service.forgot_password(email)
    return templates.TemplateResponse(f"{template_prefix}/request-reset.html", context)


@router.get(
    path="/reset-password",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def get_reset_password(
    request: Request,
    token: str,
):
    context = {"request": request, "token": token}
    return templates.TemplateResponse(f"{template_prefix}/reset-password.html", context)


@router.post("/reset-password/", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    context = {"request": request}

    try:
        await user_service.reset_password(password, token)
    except exceptions.InvalidResetPasswordToken as e:
        raise HTTPException(
            status_code=400, detail="Invalid reset password token."
        ) from e
    except exceptions.UserInactive as e:
        raise HTTPException(status_code=400, detail="User is inactive.") from e
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(status_code=400, detail="Invalid password.") from e

    return templates.TemplateResponse(f"{template_prefix}/login.html", context)


@router.post("/forgot-password/", response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    email: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    context = {"request": request}

    await user_service.forgot_password(email)
    return templates.TemplateResponse(f"{template_prefix}/request-reset.html", context)
