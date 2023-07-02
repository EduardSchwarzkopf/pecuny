from fastapi import FastAPI, Request, status
from app.routes import router_list

from app.database import db

from app import schemas, templates
import arel
import os


# from .routers import users, posts, auth, vote
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.utils.exceptions import UnauthorizedPageException
from app.middleware import HeaderLinkMiddleware
from app.utils import BreadcrumbBuilder


from starlette_wtf import CSRFProtectMiddleware
from starlette.middleware.sessions import SessionMiddleware

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

app.add_middleware(SessionMiddleware, secret_key="***REPLACEME1***")
app.add_middleware(CSRFProtectMiddleware, csrf_secret="***REPLACEME2***")


@app.middleware("http")
async def add_breadcrumbs(request: Request, call_next):
    breadcrumb_builder = BreadcrumbBuilder(request)
    breadcrumb_builder.add("Home", "/")

    # store the breadcrumb builder in the request state so it can be accessed in the route handlers
    request.state.breadcrumb_builder = breadcrumb_builder

    return await call_next(request)


if _debug := os.getenv("DEBUG"):
    hot_reload = arel.HotReload(paths=[arel.Path(".")])
    app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")
    app.add_event_handler("startup", hot_reload.startup)
    app.add_event_handler("shutdown", hot_reload.shutdown)
    templates.env.globals["DEBUG"] = _debug
    templates.env.globals["hot_reload"] = hot_reload


# Exception Handlers
@app.exception_handler(401)
async def unauthorized_exception_handler(
    request: Request, exc: UnauthorizedPageException
):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        "pages/auth/page_login.html",
        {
            "request": request,
            "redirect": request.url.path,
            "form": schemas.LoginForm(request),
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
        )

    return templates.TemplateResponse(
        "exceptions/422.html",
        {"request": request},
        status_code=status_code,
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


for route in router_list:
    app.include_router(
        route["router"], prefix=route.get("prefix", ""), tags=route.get("tags", [])
    )
