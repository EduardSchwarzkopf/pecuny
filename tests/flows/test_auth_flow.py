from httpx import Cookies
from starlette.status import HTTP_200_OK

from app import models, schemas
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_flow_logout(test_user: models.User):
    """
    Test function to verify the logout process for a test user.

    Args:
        test_user (fixture): The test user object for logout testing.
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
        url="/dashboard/",
        method=RequestMethod.GET,
        cookies=cookies,
        follow_redirects=True,
    )

    assert res.status_code == HTTP_200_OK
    assert res.url.path == "/login"


async def test_flow_login(test_user: models.User, test_user_data: schemas.UserCreate):
    """
    Test function to verify the login process for a test user.

    Args:
        test_user (fixture): The test user object for login testing.
    """

    res = await make_http_request(
        url="/login",
        method=RequestMethod.POST,
        data={"username": test_user.email, "password": test_user_data.password},
    )

    cookies: Cookies = res.cookies
    access_token = cookies.get(settings.access_token_name)
    refresh_token = cookies.get(settings.refresh_token_name)

    assert access_token is not None
    assert refresh_token is not None

    res = await make_http_request(
        url="/dashboard/",
        method=RequestMethod.GET,
        cookies=cookies,
        follow_redirects=True,
    )

    assert res.status_code == HTTP_200_OK
