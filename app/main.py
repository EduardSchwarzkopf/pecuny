from fastapi import FastAPI, Request
import fastapi_users
from app.routers.api import (
    accounts,
    transactions,
    users,
    categories,
    scheduled_transactions,
)

from app.routers import home
from app.database import db
from app.routers import auth
from app.schemas import UserCreate, UserRead, UserUpdate
from app.auth_manager import auth_backend, fastapi_users
from app import templates


# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from app.utils.exceptions import UnauthorizedPageException

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Allowed Domains to talk to this api
origins = ["http://127.0.0.1:5173", "http://127.0.0.1"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(401)
async def unauthorized_exception_handler(
    request: Request, exc: UnauthorizedPageException
):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        "pages/auth/login.html",
        {"request": request, "redirect": request.url.path},
        status_code=exc.status_code,
    )


@app.exception_handler(404)
async def page_not_found_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        "exceptions/404.html",
        {"request": request},
        status_code=exc.status_code,
    )


@app.on_event("startup")
async def startup_event():
    await db.init()
    await db.create_all()


@app.on_event("shutdown")
async def shutdown_event():
    await db.session.close()


# Page Routes
app.include_router(home.router)
app.include_router(auth.router)

# API Routes
api_prefix = "/api"
app.include_router(
    accounts.router,
    prefix=f"{api_prefix}/accounts",
    tags=["Accounts"],
)
app.include_router(
    transactions.router,
    prefix=f"{api_prefix}/transactions",
    tags=["Transactions"],
)
app.include_router(
    scheduled_transactions.router,
    prefix=f"{api_prefix}/scheduled-transactions",
    tags=["Scheduled transactions"],
)
app.include_router(
    categories.router,
    prefix=f"{api_prefix}/categories",
    tags=["Categories"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=f"{api_prefix}/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix=f"{api_prefix}/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix=f"{api_prefix}/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix=f"{api_prefix}/auth",
    tags=["Auth"],
)

app.include_router(
    users.router,
    prefix=f"{api_prefix}/users",
    tags=["Users"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix=f"{api_prefix}/users",
    tags=["Users"],
)
