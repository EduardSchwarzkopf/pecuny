from fastapi import HTTPException, status


class UserAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("User with given email already exists.")


class PasswordsDontMatchException(Exception):
    def __init__(self):
        super().__init__("Provided passwords do not match.")


class UserNotFoundException(Exception):
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

    pass
