from app.models import User
from fastapi import Request, Depends


from app.auth_manager import current_active_user
from app.utils import PageRouter
from app.utils.template_utils import render_template
from app.services import accounts as service

router = PageRouter(tags=["Dashboard"])


@router.get("/")
async def dashboard(
    request: Request,
    user: User = Depends(current_active_user),
):
    account_data = await service.get_accounts(user)
    return render_template(
        "pages/dashboard/page_multiple_accounts.html",
        request,
        {"accounts": account_data},
    )
