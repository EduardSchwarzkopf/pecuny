from enum import Enum


class EmailVerificationStatus(Enum):
    VERIFIED = 1
    INVALID_TOKEN = 0
    ALREADY_VERIFIED = -1


class FeedbackType(Enum):
    ERROR = "error"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"


class RequestMethod(Enum):
    GET = "get"
    POST = "post"
    PATCH = "patch"
    DELETE = "delete"


class DatabaseFilterOperator(Enum):
    EQUAL = "="
    NOT_EQUAL = "<>"
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LIKE = "LIKE"
