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
    status_code: int, expected_status_code: Optional[int] = None
):
    """
    Asserts the error response received from an HTTP request.

    Args:
        status_code: The expected status code of the response.
        expected_status_code: The optional expected status code to compare with the response status code.
    """

    res = await make_http_request(
        f"/api/errors/raise/{status_code}", method=RequestMethod.GET
    )

    if expected_status_code:
        assert res.status_code == expected_status_code
    else:
        assert res.status_code == status_code

    json_response = res.json()

    assert "detail" in json_response


async def test_api_not_found_error():
    """
    Sends an HTTP GET request to the "/api/not-found" endpoint with follow redirects enabled.
    """

    res = await make_http_request(
        "/api/not-found", follow_redirects=True, method=RequestMethod.GET
    )

    assert res.status_code == HTTP_404_NOT_FOUND
    json_response = res.json()

    assert "detail" in json_response


async def test_api_internal_server_error():
    """
    Tests the API behavior for an internal server error response.
    """
    await assert_error_response(HTTP_500_INTERNAL_SERVER_ERROR)


async def test_api_unauthorized_error():
    """
    Tests the API behavior for an unauthorized error response.
    """
    await assert_error_response(HTTP_401_UNAUTHORIZED)


async def test_api_request_validation_error():
    """
    Tests the API behavior for a request validation error response.
    """
    await assert_error_response(HTTP_422_UNPROCESSABLE_ENTITY)


async def test_api_forbidden_error():
    """
    Tests the API behavior for a forbidden error response.
    """
    await assert_error_response(HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND)


async def test_api_method_not_allowed():
    """
    Tests the API behavior for a method not allowed error response.
    """
    await assert_error_response(HTTP_405_METHOD_NOT_ALLOWED)
