from typing import List

from fastapi import Request

from app import models
from app.config import settings
from app.services.accounts import AccountService
from app.utils.template_utils import render_template

service = AccountService()


def calculate_total_balance(account_list: List[models.Account]) -> float:
    """
    Calculates the total balance of a list of accounts.

    Args:
        account_list: A list of account objects.

    Returns:
        float: The total balance of the accounts.
    """

    return sum(account.balance for account in account_list)


def has_user_access_to_account(user: models.User, account: models.Account) -> bool:
    """
    Check if the user has access to the account.

    Args:
        user: The user object.
        account: The account object.

    Returns:
        bool: True if the user has access to the account, False otherwise.
    """
    return user.id == account.user_id


async def get_account_list_template(
    user: models.User, template_name: str, request: Request
):
    """
    Renders an account list template.

    Args:
        user: The user object.
        template_name: The name of the template.
        request: The request object.

    Returns:
        The rendered template.

    Raises:
        None
    """

    account_list = await service.get_accounts(user) or []
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
