from typing import Optional

from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def assert_error_response(
    status_code: int, excpected_status_code: Optional[int] = None
):
    res = await make_http_request(
        f"/api/errors/raise/{status_code}", method=RequestMethod.GET
    )

    if excpected_status_code:
        assert res.status_code == excpected_status_code
    else:
        assert res.status_code == status_code

    json_response = res.json()

    assert "detail" in json_response


async def test_api_not_found_error():
    res = await make_http_request(
        "/api/not-found", follow_redirects=True, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND
    json_response = res.json()

    assert "detail" in json_response


async def test_api_internal_server_error():
    await assert_error_response(HTTP_500_INTERNAL_SERVER_ERROR)


async def test_api_unauthorized_error():
    await assert_error_response(HTTP_401_UNAUTHORIZED)


async def test_api_request_validation_error():
    await assert_error_response(HTTP_422_UNPROCESSABLE_ENTITY)


async def test_api_forbidden_error():
    await assert_error_response(HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND)


async def test_api_method_not_allowed():
    await assert_error_response(HTTP_405_METHOD_NOT_ALLOWED)
