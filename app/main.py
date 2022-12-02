from fastapi import FastAPI
import fastapi_users
from .routers import accounts, transactions, users
from app.database import db
from app.schemas import UserCreate, UserRead, UserUpdate
from app.routers.users import auth_backend, fastapi_users

# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowed Domains to talk to this api
origins = ["http://localhost:5173", "http://localhost"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await db.init()
    await db.create_all()


@app.on_event("shutdown")
async def shutdown_event():
    await db.session.close()


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
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["Auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)
