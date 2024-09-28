from fastapi.responses import RedirectResponse

from app.config import settings
from app.exceptions.http_exceptions import raise_http_error
from app.utils import APIRouterExtended

router = APIRouterExtended(tags=["Errors"], prefix="/errors")


@router.get("/raise/{status_code}")
async def raise_error(status_code: int):
    if settings.environment != "test":
        return RedirectResponse("/", status_code=302)

    raise_http_error(status_code)
