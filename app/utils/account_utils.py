from typing import List

from app import models


def calculate_total_balance(account_list: List[models.Account]) -> float:
    """
    Calculates the total balance of a list of accounts.

    Args:
        account_list: A list of account objects.

    Returns:
        float: The total balance of the accounts.
    """

    return sum(account.balance for account in account_list)
