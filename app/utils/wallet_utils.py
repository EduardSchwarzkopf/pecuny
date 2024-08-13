from fastapi import Request

from app import models
from app.config import settings
from app.services.wallets import WalletService
from app.utils.template_utils import render_template


async def get_wallet_list_template(
    user: models.User, template_name: str, request: Request
):
    """
    Renders an wallet list template.

    Args:
        user: The user object.
        template_name: The name of the template.
        request: The request object.

    Returns:
        The rendered template.

    Raises:
        None
    """

    service = WalletService()
    wallet_list = await service.get_wallets(user)

    total_balance = service.calculate_total_balance(wallet_list)

    return render_template(
        template_name,
        request,
        {
            "wallet_list": wallet_list,
            "max_allowed_wallets": settings.max_allowed_wallets,
            "total_balance": total_balance,
        },
    )
