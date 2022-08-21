from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware
from .database import SQLALCHEMY_DATABASE_URL
from .routers import users, auth, accounts, transactions

# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)


@app.get("/")
async def root():
    return {"message": "Hello, new stuff"}
