from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi_users import exceptions

from app import templates
from app.auth_manager import UserManager, fastapi_users, get_user_manager
from app.services.users import UserService

current_active_user = fastapi_users.current_user(optional=True)

router = APIRouter()
template_prefix = "pages/auth"


async def get_user_service(
    user_manager: UserManager = Depends(get_user_manager),
) -> UserService:
    return UserService(user_manager)


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
        context["error"] = "Email already in use"
        return templates.TemplateResponse(f"{template_prefix}/register.html", context)

    if password != password_confirm:
        context["error"] = "Passwords do not match"
        return templates.TemplateResponse(f"{template_prefix}/register.html", context)

    result = await user_service.create_user(email, displayname, password)
    return templates.TemplateResponse(f"{template_prefix}/login.html", context)


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

    result = await user_service.forgot_password(email)
    return templates.TemplateResponse(f"{template_prefix}/request-reset.html", context)
