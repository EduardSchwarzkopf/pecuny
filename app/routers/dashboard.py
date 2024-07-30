from fastapi import Depends
from fastapi.responses import RedirectResponse

from app.auth_manager import current_active_verified_user
from app.models import User
from app.tasks import process_scheduled_transactions
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
        RedirectResponse: A redirect response to the accounts page.
    """

    # TODO: Create a usueful dashboard page

    return RedirectResponse(f"{router.prefix}/accounts", status_code=302)


@router.get("/test")
async def page_dashboard_test():
    process_scheduled_transactions.delay()
    return {"message": "Hello World"}
