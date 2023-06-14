from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import settings
from fastapi.exceptions import HTTPException
from starlette import status
from app.utils import PageRouter
from app.utils.template_utils import render_template
from app import schemas, transaction_manager as tm, models
from app.services import accounts as service
from app.auth_manager import current_active_user

router = PageRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/", response_class=HTMLResponse)
async def page_accounts_list(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    account_list = await service.get_accounts(user)
    return render_template(
        "pages/dashboard/page_multiple_accounts.html",
        request,
        {
            "account_list": account_list,
            "max_allowed_accounts": settings.max_allowed_accounts,
        },
    )


@router.get("/create-account", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    if service.check_max_accounts(user):
        return RedirectResponse(request.url_for("dashboard"), status_code=302)

    return render_template("pages/dashboard/page_create_account.html", request)


@router.post("/create-account")
async def page_create_account(
    request: Request,
    user: models.User = Depends(current_active_user),
    label: str = Form(...),
    description: str = Form(...),
    balance: float = Form(...),
):
    if service.check_max_accounts(user):
        return RedirectResponse(request.url_for("dashboard"), status_code=302)

    account_data = {"label": label, "description": description, "balance": balance}

    account = schemas.Account(**account_data)

    response = await tm.transaction(service.create_account, user, account)
    # TODO: Error handling

    return RedirectResponse(
        router.url_path_for("page_create_account_form"), status_code=302
    )


@router.get("/{account_id}")
async def page_get_account(
    request: Request,
    account_id: int,
    current_user: models.User = Depends(current_active_user),
):
    account = await service.get_account(current_user, account_id)

    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    return render_template(
        "pages/dashboard/page_single_account.html", request, {"account": account}
    )
