from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError


def raise_http_error(status_code: int):
    """
    Raises an appropriate HTTP-related exception based on the provided status code.

    Args:
        status_code: The HTTP status code to determine the type of exception to raise.

    Raises:
        HTTPBadRequestException: If status_code is 400.
        HTTPUnauthorizedException: If status_code is 401.
        HTTPForbiddenException: If status_code is 403.
        HTTPNotFoundException: If status_code is 404.
        HTTPMethodNotAllowedException: If status_code is 405.
        RequestValidationError: If status_code is 422.
        HTTPInternalServerException: If status_code is 500.
        Exception: If status_code is 666.
        HTTPException: If status_code does not match any specific exception.
    """

    if status_code == 400:
        raise HTTPBadRequestException()

    if status_code == 401:
        raise HTTPUnauthorizedException()

    if status_code == 403:
        raise HTTPForbiddenException()

    if status_code == 404:
        raise HTTPNotFoundException()

    if status_code == 405:
        raise HTTPMethodNotAllowedException()

    if status_code == 422:
        raise RequestValidationError([])

    if status_code == 500:
        raise HTTPInternalServerException()

    if status_code == 666:
        # pylint: disable=broad-exception-raised
        raise Exception(  # sourcery skip: raise-specific-error
            "This is a custom exception."
        )

    raise HTTPException(status_code=status_code, detail="Custom error")


class HTTPUnauthorizedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized.",
        )


class HTTPForbiddenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to do this.",
        )


class HTTPNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This is not the resource you are looking for.",
        )


class HTTPBadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad Request."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class HTTPInternalServerException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )


class HTTPMethodNotAllowedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="This method is not allowed.",
        )
