from httpx import Cookies
from starlette.status import HTTP_401_UNAUTHORIZED

from app import models
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_flow_logout(test_user: models.User):
    """
    Test function to verify the logout process for a test user.

    Args:
        test_user: The test user object for logout testing.

    Returns:
        None
    """

    res = await make_http_request(
        url="/logout", method=RequestMethod.GET, as_user=test_user
    )

    cookies: Cookies = res.cookies
    access_token = cookies.get(settings.access_token_name)
    refresh_token = cookies.get(settings.refresh_token_name)

    assert access_token == '""'
    assert refresh_token == '""'

    res = await make_http_request(
        url="/dashboard/", method=RequestMethod.GET, cookies=cookies
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED
