from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from starlette_wtf import csrf_protect

from app import schemas
from app.auth_manager import current_active_user
from app.models import User
from app.services.users import UserService
from app.utils import PageRouter
from app.utils.enums import FeedbackType
from app.utils.template_utils import render_template, set_feedback

router = PageRouter(tags=["Users"], prefix="/users")


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

    return render_template(
        "pages/user/page_user_settings.html",
        request,
        {"form": form, "action_url": router.url_path_for("page_user_settings")},
    )


@csrf_protect
@router.post("/settings")
async def page_user_settings(
    request: Request,
    user: User = Depends(current_active_user),
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

    user.email = form.email.data
    user.displayname = form.displayname.data

    user_service = UserService()
    await user_service.update_user(user)

    return RedirectResponse("/", 302)
