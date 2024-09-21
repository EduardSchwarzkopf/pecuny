from app.exceptions.base_service_exception import BaseServiceException


class UserAlreadyExistsException(BaseServiceException):
    def __init__(self):
        super().__init__("User with given email already exists.")


class UserNotFoundException(BaseServiceException):
    pass
