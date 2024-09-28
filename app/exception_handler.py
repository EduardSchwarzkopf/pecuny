from typing import Union

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler as _http_exception_handler
from fastapi.exception_handlers import (
    request_validation_exception_handler as _request_validation_exception_handler,
)
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app import templates
from app.exceptions.base_service_exception import (
    EntityAccessDeniedException,
    EntityNotFoundException,
)
from app.exceptions.http_exceptions import (
    HTTPBadRequestException,
    HTTPForbiddenException,
    HTTPInternalServerException,
    HTTPMethodNotAllowedException,
    HTTPNotFoundException,
    HTTPUnauthorizedException,
)
from app.logger import get_logger

logger = get_logger(__name__)


async def unauthorized_exception_handler(
    request: Request, exc: HTTPUnauthorizedException
):
    """Exception handler for 401 Unauthorized errors.

    Args:
        request: The request object.
        exc: The HTTPUnauthorizedPageException object.

    Returns:
        Response: The response to return.
    """
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return RedirectResponse(request.url_for("login"))


async def access_denied_exception_handler(
    request: Request, exc: EntityAccessDeniedException
):
    """Exception handler for EntityAccessDeniedException.

    Args:
        request: The request object.
        exc: The EntityAccessDeniedException object.

    Returns:
        Response: The response to return.
    """

    return await http_not_found_exception_handler(request, HTTPNotFoundException())


async def forbidden_exception_handler(request: Request, exc: HTTPForbiddenException):
    """
    Handles exceptions with status code 403 (Forbidden).

    Args:
        request: The request object associated with the exception.
        exc: The UnauthorizedPageException instance raised.

    Returns:
        JSONResponse or RedirectResponse based on the request path.
    """

    return await http_not_found_exception_handler(request, HTTPNotFoundException())


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Exception handler for RequestValidationError.

    Args:
        request: The request object.
        exc: The RequestValidationError object.

    Returns:
        Response: The response to return.
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
        )

    return templates.TemplateResponse(
        request,
        "exceptions/422.html",
        status_code=status_code,
    )


async def not_found_exception_handler(request: Request, exc: EntityNotFoundException):
    return await http_not_found_exception_handler(request, HTTPNotFoundException())


async def http_404_exception_handler(request: Request, exc: HTTP_404_NOT_FOUND):
    return await http_not_found_exception_handler(request, HTTPNotFoundException())


async def http_not_found_exception_handler(
    request: Request, exc: HTTPNotFoundException
):
    """Exception handler for 404 Page Not Found errors.

    Args:
        request: The request object.
        exc: The HTTPException object.

    Returns:
        Response: The response to return.
    """
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/404.html",
        status_code=exc.status_code,
    )


async def http_bad_request_exception_handler(
    request: Request, exc: HTTPBadRequestException
):
    """Exception handler for 400 Bad Request errors.

    Args:
        request: The request object.
        exc: HTTPBadRequestException object.

    Returns:
        Response: The response to return.
    """
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/400.html",
        status_code=exc.status_code,
    )


async def http_400_exception_handler(request: Request, exc: HTTPBadRequestException):
    return await http_bad_request_exception_handler(request, HTTPBadRequestException())


async def http_405_exception_handler(
    request: Request, exc: HTTP_405_METHOD_NOT_ALLOWED
) -> JSONResponse:
    return await http_method_not_allowed_exception_handler(
        request, HTTPMethodNotAllowedException()
    )


async def http_method_not_allowed_exception_handler(
    request: Request, exc: HTTPMethodNotAllowedException
) -> JSONResponse:
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/405.html",
        status_code=exc.status_code,
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    This is a wrapper to the default RequestValidationException handler of FastAPI.
    This function will be called when client input is not valid.
    """
    logger.debug("Our custom request_validation_exception_handler was called")
    body = await request.body()
    query_params = request.query_params._dict  # pylint: disable=protected-access
    detail = {
        "errors": exc.errors(),
        "body": body.decode(),
        "query_params": query_params,
    }
    logger.info(detail)
    return await _request_validation_exception_handler(request, exc)


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> Union[JSONResponse, Response]:
    """
    This is a wrapper to the default HTTPException handler of FastAPI.
    This function will be called when a HTTPException is explicitly raised.
    """
    return await _http_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    This middleware will log all unhandled exceptions.
    Unhandled exceptions are all exceptions that are not HTTPExceptions or RequestValidationErrors.
    """
    return await internal_server_exception_handler(
        request,
        HTTPInternalServerException(),
    )


async def http_500_exception_handler(
    request: Request, exc: HTTP_500_INTERNAL_SERVER_ERROR
):
    return await internal_server_exception_handler(
        request, HTTPInternalServerException()
    )


async def internal_server_exception_handler(
    request: Request, exc: HTTPInternalServerException
):
    url = (
        f"{request.url.path}?{request.query_params}"
        if request.query_params
        else request.url.path
    )

    exception_name = exc.__class__.__name__

    logger.exception(
        f"{request.method} {url} - [500 INTERNAL SERVER ERROR] {exception_name}"
    )

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            {"detail": "Internal server error"},
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        request,
        "exceptions/500.html",
        status_code=exc.status_code,
    )
