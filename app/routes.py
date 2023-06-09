from app.routers import dashboard, accounts, auth
from app.routers.api import (
    accounts as api_accounts,
    transactions as api_transactions,
    users as api_users,
    categories as api_categories,
    scheduled_transactions as api_scheduled_transactions,
)
import fastapi_users
from app.schemas import UserCreate, UserRead, UserUpdate
from app.auth_manager import auth_backend, fastapi_users

api_prefix = "/api"

fastapi_user_routers = [
    fastapi_users.get_users_router(UserRead, UserUpdate),
    fastapi_users.get_auth_router(auth_backend),
    fastapi_users.get_register_router(UserRead, UserCreate),
    fastapi_users.get_reset_password_router(),
    fastapi_users.get_verify_router(UserRead),
]

route_list = [
    {"router": router, "prefix": f"{api_prefix}/auth", "tags": ["Api", "Auth"]}
    for router in fastapi_user_routers
]

api_routers = [
    (api_users.router, "users", ["Api", "Users"]),
    (api_categories.router, "categories", ["Api", "Categories"]),
    (api_accounts.router, "accounts", ["Api", "Accounts"]),
    (api_transactions.router, "transactions", ["Api", "Transactions"]),
    (
        api_scheduled_transactions.router,
        "scheduled-transactions",
        ["Api", "Scheduled Transactions"],
    ),
]

route_list += [
    {"router": router, "prefix": f"{api_prefix}/{name}", "tags": tags}
    for router, name, tags in api_routers
]

page_routers = [
    (dashboard.router, "", ["Page", "Dashboard"]),
    (accounts.router, "/accounts", ["Page", "Accounts"]),
    (auth.router, "/auth", ["Page", "Auth"]),
]

route_list += [
    {"router": router, "prefix": prefix, "tags": tags}
    for router, prefix, tags in page_routers
]
