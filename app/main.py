from fastapi import FastAPI, Depends
from fastapi_sqlalchemy import DBSessionMiddleware
import fastapi_users
from .database import SQLALCHEMY_DATABASE_URL, db
from .routers import accounts, transactions

from app.database import User
from app.schemas import UserCreate, UserRead, UserUpdate
from app.routers.users import auth_backend, current_active_user, fastapi_users

# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
db.init()

# Allowed Domains to talk to this api
origins = ["http://localhost"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Database
app.add_middleware(DBSessionMiddleware, db_url=SQLALCHEMY_DATABASE_URL)

# Routes
app.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["Accounts"],
)
app.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.get("/")
async def root():
    return {"message": "Hello, new stuff"}
