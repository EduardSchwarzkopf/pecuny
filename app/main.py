import os
from contextlib import asynccontextmanager

import arel
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette_wtf import CSRFProtectMiddleware

from app import schemas, templates
from app.config import settings
from app.database import db
from app.logger import get_logger
from app.middleware import HeaderLinkMiddleware
from app.routes import router_list
from app.utils import BreadcrumbBuilder
from app.utils.exceptions import UnauthorizedPageException


@asynccontextmanager
async def lifespan():
    await db.init()
    yield
    await db.session.close()


app = FastAPI(lifespan=lifespan)
logger = get_logger(__name__)

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

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.add_middleware(CSRFProtectMiddleware, csrf_secret=settings.csrf_secret)


@app.middleware("http")
async def add_breadcrumbs(request: Request, call_next):
    """Middleware to add breadcrumbs to the request state.

    Args:
        request: The request object.
        call_next: The next middleware or route handler.

    Returns:
        Response: The response from the next middleware or route handler.

    Raises:
        None
    """
    breadcrumb_builder = BreadcrumbBuilder(request)
    breadcrumb_builder.add("Dashboard", "/dashboard")

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
    """Exception handler for 401 Unauthorized errors.

    Args:
        request: The request object.
        exc: The UnauthorizedPageException object.

    Returns:
        Response: The response to return.

    Raises:
        None
    """
    logger.info("[UnauthorizedAccess] on path: %s", request.url.path)
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
    """Exception handler for RequestValidationError.

    Args:
        request: The request object.
        exc: The RequestValidationError object.

    Returns:
        Response: The response to return.

    Raises:
        None
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    logger.exception("UNPROCESSABLE_ENTITY - %s", request.__dict__)
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
    """Exception handler for 404 Page Not Found errors.

    Args:
        request: The request object.
        exc: The HTTPException object.

    Returns:
        Response: The response to return.

    Raises:
        None
    """
    logger.warning("[PageNotFound] on path: %s", request.url.path)
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return templates.TemplateResponse(
        "exceptions/404.html",
        {"request": request},
        status_code=exc.status_code,
    )


for route in router_list:
    app.include_router(
        route["router"], prefix=route.get("prefix", ""), tags=route.get("tags", [])
    )
