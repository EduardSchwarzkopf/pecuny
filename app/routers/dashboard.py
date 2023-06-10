from app.models import User
from fastapi import APIRouter, Request, Depends


from app.auth_manager import current_active_user
from app.utils import PageRouter
from app.utils.template_utils import render_template

router = PageRouter(tags=["Dashboard"])


@router.get(path="/")
async def index(
    request: Request,
    user: User = Depends(current_active_user),
):
    return render_template("pages/dashboard/view_dashboard.html", request)
