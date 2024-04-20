import contextlib

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions
from starlette_wtf import csrf_protect

from app import schemas, templates
from app.auth_manager import auth_backend, optional_current_active_verified_user
from app.authentication.dependencies import get_user_manager
from app.authentication.management import UserManager
from app.authentication.strategies import JWTStrategy
from app.models import User
from app.routers.dashboard import router as dashboard_router
from app.services.users import UserService
from app.utils import PageRouter
from app.utils.dataclasses_utils import CreateUserData
from app.utils.enums import FeedbackType
from app.utils.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.utils.template_utils import render_form_template, set_feedback

router = PageRouter()

LOGIN = "/login"
REGISTER = "/register"
VERIFY = "/verify"
NEW_TOKEN = "/get-verify-token"
FORGOT_PASSWORD = "/forgot-password"
RESET_PASSWORD = "/reset-password"

TEMPLATE_PREFIX = "pages/auth"
TEMPLATE_REGISTER = f"{TEMPLATE_PREFIX}/page_register.html"
TEMPLATE_LOGIN = f"{TEMPLATE_PREFIX}/page_login.html"


@csrf_protect
@router.get(path=LOGIN, tags=["Pages", "Authentication"])
async def get_login(
    request: Request,
    user: User = Depends(optional_current_active_verified_user),
    msg: str = "",
):
    """
    Renders the login form page.

    Args:
        request: The request object.
        user: The current active and verified user (optional).
        msg: A message to display on the page (optional).

    Returns:
        Union[RedirectResponse, TemplateResponse]:
            A redirect response to the dashboard page
            if the user is already logged in, or the rendered login form page.
    """

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

    return render_form_template(TEMPLATE_LOGIN, request, schemas.LoginForm(request))


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
    """
    Logs in the user.

    Args:
        request: The request object.
        credentials: The OAuth2 password request form.
        user_manager: The user manager.
        strategy: The JWT strategy.

    Returns:
        RedirectResponse: A redirect response to the home page.
    """

    user = await user_manager.authenticate(credentials)

    if user is None:
        set_feedback(request, FeedbackType.ERROR, "Wrong credentials provided")
        return render_form_template(TEMPLATE_LOGIN, request, schemas.LoginForm(request))

    if not user.is_active:
        set_feedback(request, FeedbackType.ERROR, "This account is not active")
        return render_form_template(TEMPLATE_LOGIN, request, schemas.LoginForm(request))

    result = await auth_backend.login(strategy, user)
    return RedirectResponse("/", 302, result.headers)


@router.get(path="/logout", tags=["Pages", "Authentication"])
async def logout():
    """
    Logs out the user.

    Args:
        None

    Returns:
        RedirectResponse: A redirect response to the login page with the user logged out.
    """

    response = RedirectResponse(LOGIN, status_code=302)
    response.set_cookie(auth_backend.transport.cookie_name, "")
    response.set_cookie(auth_backend.transport.refresh_cookie_name, "")
    return response


@csrf_protect
@router.get(
    path=REGISTER,
    tags=["Pages", "Authentication"],
)
async def get_regsiter(
    request: Request,
):
    """
    Renders the registration form page.

    Args:
        request: The request object.

    Returns:
        TemplateResponse: The rendered registration form page.
    """

    return render_form_template(
        TEMPLATE_REGISTER, request, schemas.RegisterForm(request)
    )


@csrf_protect
@router.post(REGISTER)
async def register(
    request: Request,
    user_service: UserService = Depends(UserService.get_instance),
):
    """
    Registers a new user.

    Args:
        request: The request object.
        user_service: The user service.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered registration form page or a redirect response.
    """

    form: schemas.RegisterForm = await schemas.RegisterForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_form_template(TEMPLATE_REGISTER, request, form)

    email = form.email.data
    password = form.password.data

    try:
        await user_service.validate_new_user(email)
    except UserAlreadyExistsException:
        set_feedback(request, FeedbackType.ERROR, "Email already exists")
        return render_form_template(TEMPLATE_REGISTER, request, form)

    try:
        await user_service.create_user(CreateUserData(email, password))
    except Exception:
        set_feedback(
            request, FeedbackType.ERROR, "Something went wrong! Please try again later."
        )
        return render_form_template(TEMPLATE_REGISTER, request, form)

    return RedirectResponse(f"{LOGIN}?msg=registered", 302)


@router.get(
    VERIFY,
    tags=["Pages", "Authentication"],
)
async def verify_email(
    request: Request,
    token: str,
    user_service: UserService = Depends(UserService.get_instance),
):
    """
    Verifies the email address associated with a user account.

    Args:
        request: The request object.
        token: The verification token.
        user_service: The user service.

    Returns:
        TemplateResponse: The rendered email verification page.
    """

    status = await user_service.verify_email(token)
    return templates.TemplateResponse(
        f"{TEMPLATE_PREFIX}/page_email_verify.html",
        {"request": request, "verification_status": status.value},
    )


@router.get(
    NEW_TOKEN,
)
async def get_new_token(
    request: Request,
):
    """
    Renders the get new token form page.

    Args:
        request: The request object.

    Returns:
        TemplateResponse: The rendered get new token form page.
    """

    return render_form_template(
        f"{TEMPLATE_PREFIX}/page_get_verify_token.html",
        request,
        schemas.GetNewTokenForm(request),
    )


@csrf_protect
@router.post("/send-verify-token")
async def send_new_token(
    request: Request,
    user_service: UserService = Depends(UserService.get_instance),
):
    """
    Sends a new token to the user.

    Args:
        request: The request object.
        user_service: The user service.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered get new token form page or a redirect response.
    """

    form: schemas.GetNewTokenForm = await schemas.GetNewTokenForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_form_template(
            f"{TEMPLATE_PREFIX}/page_get_verify_token.html", request, form
        )

    email = form.email.data

    try:
        user = await user_service.user_manager.get_by_email(email)
        await user_service.user_manager.request_new_token(user, request)

    except exceptions.UserInactive:
        set_feedback(request, FeedbackType.ERROR, "Not possible for this user")
        return render_form_template(
            f"{TEMPLATE_PREFIX}/page_get_verify_token.html", request, form
        )
    except exceptions.UserAlreadyVerified:
        set_feedback(request, FeedbackType.ERROR, "Not possible for this user")
        return render_form_template(
            f"{TEMPLATE_PREFIX}/page_get_verify_token.html", request, form
        )
    except exceptions.UserNotExists:
        set_feedback(request, FeedbackType.ERROR, "Not possible for this user")
        return render_form_template(
            f"{TEMPLATE_PREFIX}/page_get_verify_token.html", request, form
        )

    return RedirectResponse(f"{LOGIN}?msg=new_token_sent", 302)


@csrf_protect
@router.post(FORGOT_PASSWORD)
async def forgot_password(
    request: Request,
    user_service: UserService = Depends(UserService.get_instance),
):
    """
    Handles the forgot password request.

    Args:
        request: The request object.
        user_service: The user service.

    Returns:
        TemplateResponse: The rendered forgot password form page.
    """

    form = await schemas.ForgotPasswordForm.from_formdata(request)

    if not await form.validate_on_submit():
        return render_form_template(
            f"{TEMPLATE_PREFIX}/page_forgot_password.html", request, form
        )

    with contextlib.suppress(UserNotFoundException):
        await user_service.forgot_password(form.email.data)

    return render_form_template(
        f"{TEMPLATE_PREFIX}/page_request_reset.html", request, form
    )


@csrf_protect
@router.get(
    path=FORGOT_PASSWORD,
    tags=["Pages", "Authentication"],
)
async def get_forgot_password(
    request: Request,
):
    """
    Renders the forgot password form page.

    Args:
        request: The request object.

    Returns:
        TemplateResponse: The rendered forgot password form page.
    """

    form: schemas.ForgotPasswordForm = schemas.ForgotPasswordForm(request)
    return render_form_template(
        f"{TEMPLATE_PREFIX}/page_forgot_password.html", request, form
    )


@router.get(
    path=RESET_PASSWORD,
    tags=["Pages", "Authentication"],
)
async def get_reset_password(
    request: Request,
    token: str,
):
    """
    Renders the reset password form page.

    Args:
        request: The request object.
        token: The reset password token.

    Returns:
        TemplateResponse: The rendered reset password form page.
    """

    form = schemas.ResetPasswordForm(request, token=token)
    return render_form_template(
        f"{TEMPLATE_PREFIX}/page_reset_password.html", request, form
    )


@csrf_protect
@router.post(
    RESET_PASSWORD,
)
async def reset_password(
    request: Request,
    user_service: UserService = Depends(UserService.get_instance),
):
    """
    Resets the password for a user.

    Args:
        request: The request object.
        user_service: The user service.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered reset password form page or a redirect response.
    """

    form: schemas.ResetPasswordForm = await schemas.ResetPasswordForm.from_formdata(
        request
    )
    token = form.token.data
    reset_password_template = f"{TEMPLATE_PREFIX}/page_reset_password.html"

    if not await form.validate_on_submit():
        return render_form_template(reset_password_template, request, form)

    password = form.password.data
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
        return render_form_template(reset_password_template, request, form)

    return RedirectResponse(LOGIN, status_code=302)
