from app import templates

from app.models import User
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.auth_manager import current_active_user
from app.utils.template_utils import render_template


router = APIRouter(prefix="/dashboard", tags=["Pages", "Dashboard"])


@router.get(path="/", response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(current_active_user),
):
    return render_template(templates.TemplateResponse("pages/home.html"), request)
