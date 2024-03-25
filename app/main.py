import os
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone

import arel
import jwt
from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jwt import ExpiredSignatureError
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette_wtf import CSRFProtectMiddleware

from app import models, repository, schemas, templates
from app.auth_manager import SECURE_COOKIE, get_strategy
from app.config import settings
from app.database import db
from app.logger import get_logger
from app.middleware import HeaderLinkMiddleware
from app.routes import router_list
from app.utils import BreadcrumbBuilder
from app.utils.exceptions import UnauthorizedPageException

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_api_app: FastAPI):
    """
    Context manager for managing the lifespan of the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None

    """

    try:
        await db.init()
        yield
    finally:
        if db.session is not None:
            await db.session.close()


def get_app() -> FastAPI:
    """
    Get the FastAPI application.

    Returns:
        FastAPI: The FastAPI application.

    """

    fastapi = FastAPI(lifespan=lifespan)

    fastapi.mount("/static", StaticFiles(directory="static"), name="static")

    origins = ["http://127.0.0.1:5173", "http://127.0.0.1"]
    fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    fastapi.add_middleware(HeaderLinkMiddleware)
    fastapi.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
    fastapi.add_middleware(CSRFProtectMiddleware, csrf_secret=settings.csrf_secret)

    for route in router_list:
        fastapi.include_router(
            route["router"], prefix=route.get("prefix", ""), tags=route.get("tags", [])
        )

    return fastapi


app = get_app()


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

    setattr(request.state, "breadcrumb_builder", breadcrumb_builder)

    return await call_next(request)


@app.middleware("http")
async def token_refresh_middleware(request: Request, call_next) -> Response:
    """
    Middleware to handle token refresh for access and refresh tokens in the HTTP request.

    Args:
        request: The incoming HTTP request object.
        call_next: The callback to proceed with the request handling.

    Returns:
        Response:
            The HTTP response after handling token refresh

    Raises:
        HTTPException: If the access token is expired or the refresh token is invalid or expired.
    """

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    algorithm = settings.algorithm

    if access_token:
        with suppress(ExpiredSignatureError):

            payload = jwt.decode(
                access_token,
                settings.access_token_secret_key,
                algorithms=[algorithm],
                audience=settings.token_audience,
            )
            if payload.get("exp", 0) > datetime.now(timezone.utc).timestamp():
                return await call_next(request)
    if refresh_token:
        with suppress(ExpiredSignatureError):
            payload = jwt.decode(
                refresh_token,
                settings.refresh_token_secret_key,
                algorithms=[algorithm],
                audience=settings.token_audience,
            )
            user = await repository.get(models.User, payload["sub"])

            if user:
                strategy = get_strategy()
                new_access_token = await strategy.write_token(user)
                request.cookies.update({settings.access_token_name: new_access_token})
                response: Response = await call_next(request)
                response.set_cookie(
                    settings.access_token_name,
                    new_access_token,
                    max_age=strategy.lifetime_seconds,
                    secure=SECURE_COOKIE,
                )
                return response

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token expired and refresh token is invalid or expired",
    )


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
