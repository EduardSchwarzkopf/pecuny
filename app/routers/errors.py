from fastapi.responses import RedirectResponse

from app.config import settings
from app.exceptions.http_exceptions import HTTPInternalServerException
from app.utils import PageRouter

router = PageRouter(tags=["Error"], prefix="/error")


@router.get("/raise-internal-error")
async def raise_internal_error():
    if settings.environment == "test":
        raise HTTPInternalServerException()

    return RedirectResponse(f"/", status_code=302)
