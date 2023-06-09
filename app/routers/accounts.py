from fastapi import Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from app.utils import PageRouter
from app.utils.template_utils import render_template
from app import schemas, transaction_manager as tm, models
from app.services import accounts as service
from app.auth_manager import current_active_user

router = PageRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    account_data = await service.get_accounts(user)
    return render_template(
        "pages/dashboard/accounts.html", request, {"accounts": account_data}
    )


@router.get("/create-account", response_class=HTMLResponse)
async def page_create_account_form(
    request: Request,
    user: models.User = Depends(current_active_user),
):
    return render_template("pages/dashboard/create_account.html", request)


@router.post("/create-account")
async def page_create_account(
    user: models.User = Depends(current_active_user),
    label: str = Form(...),
    description: str = Form(...),
    balance: float = Form(...),
):
    account_data = {"label": label, "description": description, "balance": balance}

    account = schemas.Account(**account_data)

    response = await tm.transaction(service.create_account, user, account)
    # TODO: Error handling

    return RedirectResponse(
        router.url_path_for("page_create_account_form"), status_code=302
    )
