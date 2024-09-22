from pydantic import EmailStr

from app.exceptions.base_service_exception import BaseServiceException


class UserAlreadyExistsException(BaseServiceException):
    def __init__(self, email: EmailStr):
        super().__init__(f"User with email {email} already exists")


class UserNotFoundException(BaseServiceException):

    def __init__(self, email: EmailStr):
        super().__init__(f"No user found with email {email}")
