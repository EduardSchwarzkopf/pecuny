import contextlib
from fastapi import APIRouter, Depends, Form, Request, BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions
from app.utils.template_utils import render_template

from app import templates
from app.auth_manager import (
    JWTStrategy,
    UserManager,
    auth_backend,
    get_user_manager,
    optional_current_active_verified_user,
)
from app.models import User
from app.services.users import UserService

router = APIRouter()

LOGIN = "/login"
REGISTER = "/register"
VERIFY = "/verify"
NEW_TOKEN = "/get-new-token"
FORGOT_PASSWORD = "/forgot-password"
RESET_PASSWORD = "/reset-password"

TEMPLATE_PREFIX = "pages/auth"
TEMPLATE_REGISTER = f"{TEMPLATE_PREFIX}/register.html"
TEMPLATE_LOGIN = f"{TEMPLATE_PREFIX}/login.html"


async def get_user_service() -> UserService:
    return UserService()


@router.get(path=LOGIN, tags=["Pages", "Authentication"], response_class=HTMLResponse)
async def get_login(
    request: Request,
    user: User = Depends(optional_current_active_verified_user),
    msg: str = "",
):
    if user:
        return RedirectResponse("/", 302)

    feedback = None
    if msg == "new_token_sent":
        feedback = {
            "type": "success",
            "message": "New token was send, please check your email",
        }
    elif msg == "registered":
        feedback = {
            "type": "success",
            "message": "Welcome, please validate your email first!",
        }

    return render_template(TEMPLATE_LOGIN, request, feedback)


@router.post(
    LOGIN,
    response_class=RedirectResponse,
)
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    strategy: JWTStrategy = Depends(auth_backend.get_strategy),
):
    user = await user_manager.authenticate(credentials)

    if user is None:
        return render_template(
            TEMPLATE_LOGIN,
            request,
            {"type": "error", "message": "Wrong credentials provided"},
        )

    if not user.is_active:
        return render_template(
            TEMPLATE_LOGIN,
            request,
            {"type": "error", "message": "This account is not active"},
        )

    if not user.is_verified:
        return render_template(
            TEMPLATE_LOGIN,
            request,
            {"type": "error", "message": "You need to verify your email first"},
        )

    result = await auth_backend.login(strategy, user)
    return RedirectResponse("/", 302, result.headers)


@router.get(
    path=REGISTER, tags=["Pages", "Authentication"], response_class=HTMLResponse
)
async def get_regsiter(
    request: Request,
):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(TEMPLATE_REGISTER, context)


@router.post(REGISTER, response_class=HTMLResponse)
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

    context = {"request": request, "email": email, "displayname": displayname}

    if existing_user is not None:
        return render_template(
            TEMPLATE_REGISTER,
            request,
            {"type": "error", "message": "Email already exists"},
        )

    if password != password_confirm:
        context["feedback_type"] = "error"
        context["feedback_message"] = "Passwords do not match"
        return render_template(
            TEMPLATE_REGISTER,
            request,
            {"type": "error", "message": "Passwords do not match"},
        )

    await user_service.create_user(email, displayname, password)
    return RedirectResponse("/login?msg=registered")


@router.get(
    path=VERIFY,
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
        {"request": request, "verification_status": status.value},
    )


@router.get(NEW_TOKEN, response_class=HTMLResponse)
async def get_new_token(
    request: Request,
):
    context = {"request": request}
    return templates.TemplateResponse(f"{template_prefix}/get-new-token.html", context)


@router.post("/send-new-token", response_class=HTMLResponse)
async def send_new_token(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    with contextlib.suppress(exceptions.UserNotExists):
        user = await user_service.user_manager.get_by_email(email)
        background_tasks.add_task(user_service.request_verification, user)
    return RedirectResponse("/login?msg=new_token_sent", 302)


@router.get(
    path=FORGOT_PASSWORD,
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


@router.post(FORGOT_PASSWORD, response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    email: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    context = {"request": request}

    await user_service.forgot_password(email)
    return templates.TemplateResponse(f"{template_prefix}/request-reset.html", context)


@router.get(
    path=RESET_PASSWORD,
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def get_reset_password(
    request: Request,
    token: str,
):
    context = {"request": request, "token": token}
    return templates.TemplateResponse(f"{template_prefix}/reset-password.html", context)


@router.post(RESET_PASSWORD, response_class=HTMLResponse)
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

    return templates.TemplateResponse(TEMPLATE_LOGIN, context)
