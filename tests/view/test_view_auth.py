from bs4 import BeautifulSoup
from starlette.status import HTTP_200_OK

from app.utils.enums import RequestMethod
from tests.form_utils import base_form_test
from tests.utils import make_http_request


async def test_view_register():

    url = "/register"
    res = await make_http_request(url=url, method=RequestMethod.GET)

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    base_form_test(form, url)

    assert len(form.find_all("input")) == 3

    email_field = form.find("input", id="email")

    assert email_field["onkeyup"] == "hideError(this)"
    assert int(email_field["maxlength"]) == 320

    password_field = form.find("input", id="password")

    assert password_field["onkeyup"] == "hideError(this)"
    assert password_field["type"] == "password"


async def test_view_login():

    url = "/login"
    res = await make_http_request(url=url, method=RequestMethod.GET)

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    base_form_test(form, url)

    assert len(form.find_all("input")) == 3

    username_field = form.find("input", id="username")

    assert username_field["onkeyup"] == "hideError(this)"

    password_field = form.find("input", id="password")

    assert password_field["onkeyup"] == "hideError(this)"
    assert password_field["type"] == "password"


async def test_view_forgot_password():

    url = "/forgot-password"
    res = await make_http_request(url=url, method=RequestMethod.GET)

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    base_form_test(form, url)

    assert len(form.find_all("input")) == 2

    email_field = form.find("input", id="email")

    assert email_field["onkeyup"] == "hideError(this)"


async def test_view_forgot_password():

    res = await make_http_request(url="/get-verify-token", method=RequestMethod.GET)

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    base_form_test(form, "send-verify-token")

    assert len(form.find_all("input")) == 2

    email_field = form.find("input", id="email")

    assert email_field["onkeyup"] == "hideError(this)"


async def test_view_reset_password():

    url = "/reset-password"
    token_value = "test"
    res = await make_http_request(
        url=url, method=RequestMethod.GET, params={"token": token_value}
    )

    assert res.status_code == HTTP_200_OK

    text = res.text
    soup = BeautifulSoup(text)

    form = soup.find("form")
    base_form_test(form, url)

    assert len(form.find_all("input")) == 3

    password_field = form.find("input", id="password")

    assert password_field["type"] == "password"

    token_field = form.find("input", id="token")

    assert token_field["value"] == token_value
    assert token_field["type"] == "hidden"
