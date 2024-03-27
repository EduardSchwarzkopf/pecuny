from httpx import Cookies

from app import models
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

# async def test_create_user():
#     pass


# async def test_invalid_create_user():
#     pass


# async def test_updated_user():
#     pass


# async def test_login():
#     pass


# async def test_invalid_api_login():
#     pass


async def test_logout(test_user: models.User):
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
