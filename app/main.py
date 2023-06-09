from fastapi import FastAPI, Request
from app.routes import route_list

from app.database import db

from app import templates


# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from app.utils.exceptions import UnauthorizedPageException
from app.middleware import HeaderLinkMiddleware

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

app.add_middleware(HeaderLinkMiddleware)


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


for route in route_list:
    app.include_router(route["router"], prefix=route["prefix"], tags=route["tags"])
