from abc import ABC

from fastapi import HTTPException, status


class BaseException(ABC, Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def details(self, message):
        return f"{type(self).__name__} at line {self.__traceback__.tb_lineno} of {__file__}: {self}"


class UserAlreadyExistsException(BaseException):
    def __init__(self):
        super().__init__("User with given email already exists.")


class UserNotFoundException(BaseException):
    pass


class UnauthorizedException(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Unauthorized")


class UnauthorizedPageException(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Unauthorized")


class ForbiddenException(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Forbidden")


class NotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Not Found")


class AccessDeniedError(Exception):
    """Raised when a user tries to access a resource they don't have permission to."""
