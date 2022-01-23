from fastapi import FastAPI
from . import models
from .database import engine

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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
# app.include_router(users.router)


@app.get("/")
async def root():
    return {"message": "Hello, new stuff"}
