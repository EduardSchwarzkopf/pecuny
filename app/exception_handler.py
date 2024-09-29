from typing import Type, TypeVar, Union

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response

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
HTTPExceptionT = TypeVar("HTTPExceptionT", bound=HTTPException)


async def __get_http_exception(
    exc_class_or_status_code: int | HTTPExceptionT, exception: Type[HTTPExceptionT]
) -> HTTPExceptionT:
    """
    Returns an HTTP exception instance based on the input.

    Args:
        exc_class_or_status_code: HTTP status code or exception class.
        exception: Exception type to instantiate if status code is provided.

    Returns:
        An instance of the HTTP exception.
    """

    if isinstance(exc_class_or_status_code, int):
        return exception()

    return exc_class_or_status_code


async def unauthorized_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPUnauthorizedException
):

    exc = await __get_http_exception(
        exc_class_or_status_code, HTTPUnauthorizedException
    )

    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return RedirectResponse(request.url_for("login"))


async def entity_not_found_exception_handler(
    request: Request, exc: EntityNotFoundException
):
    """
    Handles unauthorized exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPUnauthorizedException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def entity_access_denied_exception_handler(
    request: Request, exc: EntityAccessDeniedException
):
    """
    Handles access denied exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc: EntityAccessDeniedException.

    Returns:
        JSONResponse for API requests, or RedirectResponse for non-API requests.
    """

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def forbidden_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPForbiddenException
):
    """
    Handles access forbidden exception for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPNotFoundException.


    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def validation_exception_handler(
    request: Request, exc_class_or_status_code: int | RequestValidationError
):
    """
    Handles validation exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or RequestValidationError.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    exc = exc_class_or_status_code

    if isinstance(exc, int):
        exc = RequestValidationError([])

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


async def not_found_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPNotFoundException
):
    """
    Handles validation exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPNotFoundException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    exc = await __get_http_exception(exc_class_or_status_code, HTTPNotFoundException)
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/404.html",
        status_code=exc.status_code,
    )


async def bad_request_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPBadRequestException
):
    """
    Handles validation exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPBadRequestException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """
    exc = await __get_http_exception(exc_class_or_status_code, HTTPBadRequestException)

    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/400.html",
        status_code=exc.status_code,
    )


async def method_not_allowed_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPMethodNotAllowedException
) -> JSONResponse:
    """
    Handles validation exceptions for both API and non-API requests.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPMethodNotAllowedException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    exc = await __get_http_exception(
        exc_class_or_status_code, HTTPMethodNotAllowedException
    )

    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        request,
        "exceptions/405.html",
        status_code=exc.status_code,
    )


async def unhandeled_http_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPException
):
    """
    Handles unhandled HTTP exceptions.

    Args:
        request: The incoming request object.
        exc_class_or_status_code: HTTP status code or HTTPException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """
    exc = await __get_http_exception(exc_class_or_status_code, HTTPException)
    return await internal_server_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc: Exception | int):
    """
    Handles general unhandled exceptions.

    Args:
        request: The incoming request object.
        exc: The exception or status code.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.
    """

    return await internal_server_exception_handler(
        request,
        HTTPInternalServerException(),
    )


async def internal_server_exception_handler(
    request: Request, exc: HTTPInternalServerException
):
    """
    Handles internal server exceptions.

    Args:
        request: The incoming request object.
        exc: The HTTPInternalServerException.

    Returns:
        JSONResponse for API requests, or TemplateResponse for non-API requests.

    Logs:
        Exception details including method, URL, and exception name.
    """

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
