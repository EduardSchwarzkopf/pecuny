from enum import Enum


class EmailVerificationStatus(Enum):
    VERIFIED = 1
    INVALID_TOKEN = 0
    ALREADY_VERIFIED = -1
