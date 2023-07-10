from fastapi import status
from fastapi.responses import RedirectResponse

from app.utils import PageRouter
from app.routers.dashboard import router as dashboard_router

router = PageRouter(tags=["Index"])


@router.get("/")
async def page_index():
    return RedirectResponse(
        dashboard_router.routes[0].path,
        status_code=status.HTTP_302_FOUND,
    )
