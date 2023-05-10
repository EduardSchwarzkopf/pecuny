from app import templates

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get(path="/", tags=["Pages"], response_class=HTMLResponse)
async def index(
    request: Request,
):
    context = {"request": request}
    return templates.TemplateResponse("pages/home.html", context)
