from fastapi.responses import RedirectResponse

from app.config import settings
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/error", tags=["Error"])


@router.get("/raise-internal-error")
async def api_raise_internal_error():
    if settings.environment == "test":
        raise Exception("This is a test exception for internal server error.")

    return RedirectResponse(f"/", status_code=302)
