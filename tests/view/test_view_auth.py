from bs4 import BeautifulSoup, Tag
from httpx import QueryParams
from starlette.status import HTTP_200_OK

from app.utils.enums import RequestMethod
from tests.form_utils import base_form_test
from tests.utils import make_http_request


async def view_base_test(
    url: str,
    expected_inputs: int,
    action_url: str = None,
    email_id: str = None,
    password_id: str = None,
    username_id: str = None,
    params: QueryParams = None,
) -> Tag:
    res = await make_http_request(url=url, method=RequestMethod.GET, params=params)
    assert res.status_code == HTTP_200_OK

    soup = BeautifulSoup(res.text)

    form = soup.find("form")

    if action_url is None:
        action_url = url

    base_form_test(form, action_url)

    assert len(form.find_all("input")) == expected_inputs

    if email_id:
        email_field = form.find("input", id=email_id)
        assert email_field["onkeyup"] == "hideError(this)"

    if password_id:
        password_field = form.find("input", id=password_id)
        assert password_field["onkeyup"] == "hideError(this)"
        assert password_field["type"] == "password"

    if username_id:
        username_field = form.find("input", id=username_id)
        assert username_field["onkeyup"] == "hideError(this)"

    return form


async def test_view_register():
    await view_base_test("/register", 3, email_id="email", password_id="password")


async def test_view_login():
    await view_base_test("/login", 3, email_id="username", password_id="password")


async def test_view_forgot_password():
    await view_base_test("/forgot-password", 2, email_id="email")


async def test_view_get_verify_token():
    await view_base_test(
        "/get-verify-token", 2, action_url="send-verify-token", email_id="email"
    )


async def test_view_reset_password():
    token_value = "test"

    form = await view_base_test(
        "/reset-password", 3, password_id="password", params={"token": token_value}
    )

    token_field = form.find("input", id="token")

    assert token_field["value"] == token_value
    assert token_field["type"] == "hidden"
