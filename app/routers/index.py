from fastapi import status
from fastapi.responses import RedirectResponse

from app.routers.dashboard import router as dashboard_router
from app.utils import PageRouter

router = PageRouter(tags=["Index"])


@router.get("/")
async def page_index():
    """
    Redirects to the dashboard page.

    Args:
        None

    Returns:
        RedirectResponse: A redirect response to the dashboard page.
    """

    return RedirectResponse(
        dashboard_router.routes[0].path,
        status_code=status.HTTP_302_FOUND,
    )
