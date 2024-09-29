from fastapi.responses import RedirectResponse

from app.config import settings
from app.exceptions.http_exceptions import raise_http_error
from app.utils import APIRouterExtended

router = APIRouterExtended(tags=["Errors"], prefix="/errors")


@router.get("/raise/{status_code}")
async def raise_error(status_code: int):
    """
    Handles the endpoint to raise an error based on the provided status code.

    Args:
        status_code: The HTTP status code to determine the type of error to raise.

    Returns:
        RedirectResponse: If the environment is not "test".
        None: If the environment is "test" and an error is raised.
    """
    if settings.environment != "test":
        return RedirectResponse("/", status_code=302)

    raise_http_error(status_code)
