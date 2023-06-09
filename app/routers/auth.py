import contextlib
from fastapi import Depends, Form, Request, BackgroundTasks, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions
from app.utils.template_utils import set_feedback, render_template
from app.utils.enums import FeedbackType
from .dashboard import router as dashboard_router

from app import templates
from app.auth_manager import (
    JWTStrategy,
    UserManager,
    auth_backend,
    get_user_manager,
    optional_current_active_verified_user,
    check_password_policy,
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


@router.get(path=LOGIN, tags=["Pages", "Authentication"])
async def get_login(
    request: Request,
    user: User = Depends(optional_current_active_verified_user),
    msg: str = "",
):
    if user:
        return RedirectResponse(dashboard_router.prefix, 302)

    if msg == "new_token_sent":
        set_feedback(
            request, FeedbackType.SUCCESS, "New token was send, please check your email"
        )

    elif msg == "registered":
        set_feedback(
            request, FeedbackType.SUCCESS, "Welcome, please validate your email first!"
        )

    return render_template(TEMPLATE_LOGIN, request)


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
        set_feedback(request, FeedbackType.ERROR, "Wrong credentials provided")
        return render_template(TEMPLATE_LOGIN, request)

    if not user.is_active:
        set_feedback(request, FeedbackType.ERROR, "This account is not active")
        return render_template(TEMPLATE_LOGIN, request)

    if not user.is_verified:
        set_feedback(request, FeedbackType.ERROR, "You need to verify your email first")
        return render_template(TEMPLATE_LOGIN, request)

    result = await auth_backend.login(strategy, user)
    return RedirectResponse(dashboard_router.prefix, 302, result.headers)


@router.get(path="/logout", tags=["Pages", "Authentication"])
async def logout(
    request: Request,
):
    response = RedirectResponse(LOGIN, status_code=302)
    response.delete_cookie(auth_backend.transport.cookie_name)
    return response


@router.get(
    path=REGISTER,
    tags=["Pages", "Authentication"],
)
async def get_regsiter(
    request: Request,
):
    return render_template(TEMPLATE_REGISTER, request)


@router.post(
    REGISTER,
)
async def register(
    request: Request,
    email: str = Form(...),
    displayname: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    password_policy_error = check_password_policy(password)
    if password_policy_error is not None:
        set_feedback(request, FeedbackType.ERROR, password_policy_error)
        return render_template(TEMPLATE_REGISTER, request)

    try:
        existing_user = await user_service.user_manager.get_by_email(email)
    except exceptions.UserNotExists:
        existing_user = None

    if existing_user is not None:
        set_feedback(request, FeedbackType.ERROR, "Email already exists")
        return render_template(
            TEMPLATE_REGISTER,
            request,
        )

    if password != password_confirm:
        set_feedback(request, FeedbackType.ERROR, "Passwords do not match")
        return render_template(
            TEMPLATE_REGISTER,
            request,
        )

    await user_service.create_user(email, displayname, password)
    return RedirectResponse("/login?msg=registered")


@router.get(
    path=VERIFY,
    tags=["Pages", "Authentication"],
)
async def verify_email(
    request: Request,
    token: str,
    user_service: UserService = Depends(get_user_service),
):
    status = await user_service.verify_email(token)
    return templates.TemplateResponse(
        f"{TEMPLATE_PREFIX}/email-verify.html",
        {"request": request, "verification_status": status.value},
    )


@router.get(
    NEW_TOKEN,
)
async def get_new_token(
    request: Request,
):
    return render_template(f"{TEMPLATE_PREFIX}/get-new-token.html", request)


@router.post(
    "/send-new-token",
)
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
)
async def get_forgot_password(
    request: Request,
):
    return render_template(f"{TEMPLATE_PREFIX}/forgot-password.html", request)


@router.post(
    FORGOT_PASSWORD,
)
async def forgot_password(
    request: Request,
    email: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.forgot_password(email)
    return render_template(f"{TEMPLATE_PREFIX}/request-reset.html", request)


@router.get(
    path=RESET_PASSWORD,
    tags=["Pages", "Authentication"],
)
async def get_reset_password(
    request: Request,
    token: str,
):
    return render_template(
        f"{TEMPLATE_PREFIX}/reset-password.html",
        request,
        {"token": token},
    )


@router.post(
    RESET_PASSWORD,
)
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    user_service: UserService = Depends(get_user_service),
):
    reset_password_template = f"{TEMPLATE_PREFIX}/reset-password.html"

    password_policy_error = check_password_policy(password)
    if password_policy_error is not None:
        set_feedback(request, FeedbackType.ERROR, password_policy_error)
        return render_template(reset_password_template, request)

    error = False
    try:
        await user_service.reset_password(password, token)
    except exceptions.InvalidResetPasswordToken:
        set_feedback(request, FeedbackType.ERROR, "Invalid reset password token.")
        error = True
    except exceptions.UserInactive:
        set_feedback(request, FeedbackType.ERROR, "User is inactive.")
        error = True
    except exceptions.InvalidPasswordException:
        set_feedback(request, FeedbackType.ERROR, "Invalid password.")
        error = True

    if error:
        return render_template(reset_password_template, request, {"token": token})

    return render_template(f"{TEMPLATE_PREFIX}/login.html", request)
