from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware
from . import models, events
from .database import engine, SQLALCHEMY_DATABASE_URL
from .routers import users, auth, accounts, transactions
from fastapi_sqlalchemy import db

# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware

# create all tables that are not created yet
models.Base.metadata.create_all(bind=engine)

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


# Events
@app.on_event("startup")
async def startup_event():
    with db():
        events.create_categories(db.session)


@app.get("/")
async def root():
    return {"message": "Hello, new stuff"}
