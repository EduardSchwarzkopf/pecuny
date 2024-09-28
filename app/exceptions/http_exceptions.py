from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError


def raise_http_error(status_code: int):
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
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request.")


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
