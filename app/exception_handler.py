from typing import Type, TypeVar, Union

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler as _http_exception_handler
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

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def entity_access_denied_exception_handler(
    request: Request, exc: EntityAccessDeniedException
):

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def forbidden_exception_handler(
    request: Request, exc_class_or_status_code: int | HTTPForbiddenException
):
    """
    Handles exceptions with status code 403 (Forbidden).

    Args:
        request: The request object associated with the exception.
        exc: The UnauthorizedPageException instance raised.

    Returns:
        JSONResponse or RedirectResponse based on the request path.
    """

    return await not_found_exception_handler(request, HTTPNotFoundException())


async def validation_exception_handler(
    request: Request, exc_class_or_status_code: int | RequestValidationError
):
    """Exception handler for RequestValidationError.

    Args:
        request: The request object.
        exc: The RequestValidationError object.

    Returns:
        Response: The response to return.
    """
    exc = exc_class_or_status_code

    if isinstance(exc_class_or_status_code, int):
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
    """Exception handler for 404 Page Not Found errors.

    Args:
        request: The request object.
        exc: The HTTPException object.

    Returns:
        Response: The response to return.
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
    """Exception handler for 400 Bad Request errors.

    Args:
        request: The request object.
        exc: HTTPBadRequestException object.

    Returns:
        Response: The response to return.
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
) -> Union[JSONResponse, Response]:
    exc = await __get_http_exception(exc_class_or_status_code, HTTPException)
    return await internal_server_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc: Exception | int):

    return await internal_server_exception_handler(
        request,
        HTTPInternalServerException(),
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
