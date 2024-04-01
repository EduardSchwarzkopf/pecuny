from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from fastapi_users.exceptions import UserAlreadyExists
from starlette_wtf import csrf_protect

from app import schemas
from app.auth_manager import current_active_user
from app.authentication.dependencies import get_user_service
from app.models import User
from app.services.users import UserService
from app.utils import PageRouter
from app.utils.enums import FeedbackType
from app.utils.template_utils import render_template, set_feedback

router = PageRouter(tags=["Users"], prefix="/users")


def get_settings_response(
    user: User, request: Request, form: schemas.UpdateUserForm
) -> HTMLResponse:
    """
    Generates an HTML response for the user settings page.

    Args:
        user: The user object for which the settings page is being generated.
        request: The request object associated with the page request.
        form: The UpdateUserForm schema for updating user settings.

    Returns:
        HTMLResponse: The HTML response for the user settings page.
    """

    return render_template(
        "pages/user/page_user_settings.html",
        request,
        {
            "is_verified": user.is_verified,
            "form": form,
            "action_url": router.url_path_for("page_user_settings"),
        },
    )


@csrf_protect
@router.get("/settings")
async def page_user_settings_form(
    request: Request,
    user: User = Depends(current_active_user),
):
    """
    Renders the user settings form page.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        TemplateResponse: The rendered user settings form page.
    """

    form = schemas.UpdateUserForm(request, data=user.__dict__)

    if not user.is_verified:
        set_feedback(request, FeedbackType.ERROR, "You need to verify your email first")

    return get_settings_response(user, request, form)


@csrf_protect
@router.post("/settings")
async def page_user_settings(
    request: Request,
    user: User = Depends(current_active_user),
    service: UserService = Depends(get_user_service),
):
    """
    Handles the user settings form submission.

    Args:
        request: The request object.
        user: The current active user.

    Returns:
        Union[TemplateResponse, RedirectResponse]:
            The rendered user settings form page or a redirect response.
    """

    form = await schemas.UpdateUserForm.from_formdata(request)
    if not await form.validate_on_submit():
        for field in form.errors:
            set_feedback(request, FeedbackType.ERROR, form.errors[field][0])

        return render_template(
            "pages/user/page_user_settings.html",
            request,
            {"form": form, "action_url": router.url_path_for("page_user_settings")},
        )

    user_data = schemas.UserUpdate(**form.data)
    try:
        await service.update_user(user, user_data, request)
    except UserAlreadyExists:
        form.email.data = user.email
        set_feedback(request, FeedbackType.ERROR, "Email already exists")

    return get_settings_response(user, request, form)
