from pydantic import EmailStr

from app.exceptions.base_service_exception import BaseServiceException


class UserAlreadyExistsException(BaseServiceException):
    def __init__(self):
        super().__init__("User with email already exists")


class UserNotFoundException(BaseServiceException):

    def __init__(self):
        super().__init__("No user found with this email")
