from dataclasses import dataclass
from typing import Optional, Union

from fastapi import Request


@dataclass
class CreateUserData:
    email: str
    password: str
    displayname: Optional[str] = ""
    is_verified: Optional[bool] = False
    is_superuser: Optional[bool] = False
    is_active: Optional[bool] = True
    request: Optional[Request] = None


@dataclass
class ImportedTransaction:
    date: Optional[str]
    reference: Optional[str]
    amount: Optional[Union[float, str]]
    section: Optional[Union[str, int]]
    category: Optional[Union[str, int]]
    offset_wallet_id: Optional[int] = None


@dataclass
class FailedImportedTransaction(ImportedTransaction):
    reason: str = ""


@dataclass
class FinancialSummary:
    expenses: int = 0
    income: int = 0

    @property
    def total(self) -> int:
        """
        Calculates the total amount by subtracting expenses from income.

        Returns:
            The total amount.
        """
        return self.income - self.expenses
