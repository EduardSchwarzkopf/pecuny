from fastapi import Depends
from fastapi.responses import RedirectResponse

from app.auth_manager import current_active_verified_user
from app.models import User
from app.utils import PageRouter

router = PageRouter(tags=["Dashboard"], prefix="/dashboard")


@router.get("/")
async def page_dashboard(
    _user: User = Depends(current_active_verified_user),
):
    """
    Redirects to the dashboard page.

    Args:
        user: The current active user.

    Returns:
        RedirectResponse: A redirect response to the wallets page.
    """

    # TODO: Create a usueful dashboard page

    return RedirectResponse(f"{router.prefix}/wallets", status_code=302)
