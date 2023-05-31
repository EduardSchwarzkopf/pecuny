from app import templates

from app.models import User
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.auth_manager import current_active_user


router = APIRouter()


@router.get(path="/", tags=["Pages"], response_class=HTMLResponse)
async def index(
    request: Request,
    user: User = Depends(current_active_user),
):
    context = {"request": request}
    return templates.TemplateResponse("pages/home.html", context)
