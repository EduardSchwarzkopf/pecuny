from app.models import User
from fastapi import Request, Depends


from app.auth_manager import current_active_user
from app.utils import PageRouter
from fastapi.responses import RedirectResponse


router = PageRouter(tags=["Dashboard"], prefix="/dashboard")


@router.get("/")
async def page_dashboard(
    request: Request,
    user: User = Depends(current_active_user),
):
    # TODO: Create a usueful dashboard page
    return RedirectResponse(f"{router.prefix}/accounts", status_code=302)
