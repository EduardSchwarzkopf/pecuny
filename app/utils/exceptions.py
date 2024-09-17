from abc import ABC

from fastapi import HTTPException, status

from app.utils.fields import IdField


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


class TransactionNotFoundException(BaseException):
    def __init__(self, transaction_id: IdField):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction {transaction_id} not found")


class WalletNotFoundException(BaseException):
    def __init__(self, wallet_id: IdField):
        self.wallet_id = wallet_id
        super().__init__(f"Wallet {wallet_id} not found")


class FrequencyNotFoundException(BaseException):
    def __init__(self, frequency_id: IdField):
        self.wallet_id = frequency_id
        super().__init__(f"Frequency {frequency_id} not found")


class CategoryNotFoundException(BaseException):
    def __init__(self, category_id: IdField):
        self.wallet_id = category_id
        super().__init__(f"Category {category_id} not found")


class AccessDeniedException(BaseException):
    """Raised when a user tries to access a resource they don't have permission to."""

    def __init__(self, user_id, wallet_id: IdField):
        self.user_id = user_id
        self.wallet_id = wallet_id
        super().__init__(f"User {user_id} does not have access to wallet {wallet_id}")
