from fastapi import Depends
from fastapi.responses import RedirectResponse

from app.auth_manager import current_active_user
from app.models import User
from app.utils import PageRouter

router = PageRouter(tags=["Dashboard"], prefix="/dashboard")


@router.get("/")
async def page_dashboard(
    user: User = Depends(current_active_user),  # pylint: disable=unused-argument
):
    """
    Redirects to the dashboard page.

    Args:
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the accounts page.
    """

    # TODO: Create a usueful dashboard page

    return RedirectResponse(f"{router.prefix}/accounts", status_code=302)
