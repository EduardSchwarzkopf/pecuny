from app.routers.api import (
    accounts as api_accounts,
    transactions as api_transactions,
    users as api_users,
    categories as api_categories,
    scheduled_transactions as api_scheduled_transactions,
)

from app.routers import dashboard, accounts, auth, index, users
import fastapi_users
from app.schemas import UserCreate, UserRead, UserUpdate
from app.auth_manager import auth_backend, fastapi_users

from fastapi import APIRouter


class APIRouterExtended(APIRouter):
    def __init__(self, *args, **kwargs):
        # Ensure that a prefix always starts with "/api"
        if "prefix" in kwargs:
            kwargs["prefix"] = "/api" + kwargs["prefix"]

        # Ensure that "Api" and "Page" are always included in tags
        if "tags" in kwargs:
            if "Api" not in kwargs["tags"]:
                kwargs["tags"].append("Api")
            if "Page" not in kwargs["tags"]:
                kwargs["tags"].append("Page")

        super().__init__(*args, **kwargs)


api_prefix = "/api"
auth_tag_list = ["Api", "Auth"]
user_tag_list = ["Api", "Users"]

router_list = [
    ## Pages
    {"router": index.router},
    {"router": dashboard.router},
    {"router": accounts.router},
    {"router": auth.router},
    {"router": users.router},
    ## Api
    {
        "router": api_users.router,
    },
    {"router": api_categories.router},
    {
        "router": api_accounts.router,
    },
    {
        "router": api_transactions.router,
    },
    {
        "router": api_scheduled_transactions.router,
    },
    ## Fastapi Users
    {
        "router": fastapi_users.get_users_router(UserRead, UserUpdate),
        "prefix": f"{api_prefix}/users",
        "tags": user_tag_list,
    },
    {
        "router": fastapi_users.get_auth_router(auth_backend),
        "prefix": f"{api_prefix}/auth",
        "tags": auth_tag_list,
    },
    {
        "router": fastapi_users.get_register_router(UserRead, UserCreate),
        "prefix": f"{api_prefix}/auth",
        "tags": auth_tag_list,
    },
    {
        "router": fastapi_users.get_reset_password_router(),
        "prefix": f"{api_prefix}/auth",
        "tags": auth_tag_list,
    },
    {
        "router": fastapi_users.get_verify_router(UserRead),
        "prefix": f"{api_prefix}/auth",
        "tags": auth_tag_list,
    },
]
