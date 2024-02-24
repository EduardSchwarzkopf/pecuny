from typing import List

from fastapi import Request

from app import models
from app.config import settings
from app.services import accounts as service
from app.utils.log_messages import ACCOUNT_USER_ID_MISMATCH
from app.utils.template_utils import render_template


def calculate_total_balance(account_list: List[models.Account]) -> float:
    """
    Calculates the total balance of a list of accounts.

    Args:
        account_list: A list of account objects.

    Returns:
        float: The total balance of the accounts.
    """

    return sum(account.balance for account in account_list)


async def get_account_list_template(
    user: models.User, template_name: str, request: Request
):
    account_list = await service.get_accounts(user)
    total_balance = calculate_total_balance(account_list)

    return render_template(
        template_name,
        request,
        {
            "account_list": account_list,
            "max_allowed_accounts": settings.max_allowed_accounts,
            "total_balance": total_balance,
        },
    )
