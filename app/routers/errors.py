from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse

from app.config import settings
from app.exceptions.http_exceptions import (
    HTTPBadRequestException,
    HTTPForbiddenException,
    HTTPInternalServerException,
    HTTPNotFoundException,
    HTTPUnauthorizedException,
)
from app.utils import PageRouter

router = PageRouter(tags=["Error"], prefix="/errors")


@router.get("/raise/{status_code}")
async def raise_error(status_code: int):
    # if settings.environment != "test":
    #     return RedirectResponse(f"/", status_code=302)

    if status_code == 422:
        raise RequestValidationError([])

    if status_code == 400:
        raise HTTPBadRequestException()

    if status_code == 500:
        raise HTTPInternalServerException()

    if status_code == 404:
        raise HTTPNotFoundException()

    if status_code == 403:
        raise HTTPForbiddenException()

    if status_code == 401:
        raise HTTPUnauthorizedException()

    raise HTTPException(status_code=status_code, detail="Custom error")
