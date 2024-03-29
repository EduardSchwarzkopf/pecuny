from typing import Union

import fastapi_users
from fastapi import APIRouter

from app.auth_manager import auth_backend, fastapi_users
from app.routers import accounts, auth, dashboard, index, transactions, users
from app.routers.api import accounts as api_accounts
from app.routers.api import auth as api_auth
from app.routers.api import categories as api_categories
from app.routers.api import scheduled_transactions as api_scheduled_transactions
from app.routers.api import transactions as api_transactions
from app.routers.api import users as api_users
from app.schemas import UserRead, UserUpdate

RouterConfig = dict[str, Union[APIRouter, str, list[str]]]
RouterList = list[RouterConfig]


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


API_PREFIX = "/api"
auth_tag_list = ["Api", "Auth"]
user_tag_list = ["Api", "Users"]

router_list: RouterList = [
    ## Pages
    {"router": index.router},
    {"router": dashboard.router},
    {"router": accounts.router},
    {"router": auth.router},
    {"router": users.router},
    {"router": transactions.router},
    ## Api
    {
        "router": api_users.router,
    },
    {"router": api_categories.router},
    {"router": api_auth.router},
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
        "prefix": f"{API_PREFIX}/users",
        "tags": user_tag_list,
    },
    {
        "router": fastapi_users.get_auth_router(auth_backend),
        "prefix": f"{API_PREFIX}/auth",
        "tags": auth_tag_list,
    },
    {
        "router": fastapi_users.get_reset_password_router(),
        "prefix": f"{API_PREFIX}/auth",
        "tags": auth_tag_list,
    },
    {
        "router": fastapi_users.get_verify_router(UserRead),
        "prefix": f"{API_PREFIX}/auth",
        "tags": auth_tag_list,
    },
]
