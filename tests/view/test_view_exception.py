from bs4 import BeautifulSoup
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_view_not_found_error():
    res = await make_http_request(
        "/not-found", follow_redirects=True, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND

    soup = BeautifulSoup(res.text, features="html.parser")

    home_link = soup.find("a", {"href": "/"})
    assert home_link is not None


async def test_view_internal_server_error():
    res = await make_http_request("/error/raise/500", method=RequestMethod.GET)

    assert res.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    soup = BeautifulSoup(res.text, features="html.parser")

    assert soup.find("h1").text == "✖⸑✖"


async def test_view_request_validation_error():
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    res = await make_http_request(
        f"/errors/raise/{status_code}", method=RequestMethod.GET
    )

    assert res.status_code == status_code

    soup = BeautifulSoup(res.text, features="html.parser")

    assert soup.find("p") is not None
    assert soup.find("a", {"href": "/"}) is not None


async def test_view_forbidden_error():
    res = await make_http_request(
        f"/errors/raise/{HTTP_403_FORBIDDEN}", method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND
    soup = BeautifulSoup(res.text, features="html.parser")

    assert soup.find("a", {"href": "/"}) is not None


def test_view_timeout_error():
    pass


def test_create_invalid_data():
    raise NotImplementedError()


def test_view_method_not_allowed():
    raise NotImplementedError()
