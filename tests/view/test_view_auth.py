from bs4 import BeautifulSoup
from httpx import Cookies
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from app import models
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_view_register():

    url = "/register"
    res = await make_http_request(url=url, method=RequestMethod.GET)

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    assert form["method"] == "POST"
    assert url in form["action"]

    csrf_field = form.find("input", id="csrf_token")
    csrf_attr = csrf_field.attrs
    assert csrf_attr["type"] == "hidden"
    assert csrf_attr["name"] == "csrf_token"
    assert bool(csrf_attr["value"].strip())

    email_field = form.find("input", id="email")

    assert email_field["onkeyup"] == "hideError(this)"
    assert int(email_field["maxlength"]) == 320

    password_field = form.find("input", id="password")

    assert password_field["onkeyup"] == "hideError(this)"
    assert password_field["type"] == "password"


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

    res = await make_http_request(
        url="/dashboard", method=RequestMethod.GET, cookies=cookies
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED
