import uuid

from fastapi_users import FastAPIUsers

from app.authentication.dependencies import get_strategy, get_user_manager
from app.authentication.strategies import JWTAuthBackend, TokensCookieTransport
from app.config import settings
from app.models import User

cookie_transport = TokensCookieTransport(
    cookie_name=settings.access_token_name,
    cookie_max_age=settings.access_token_expire_minutes,
    cookie_refresh_max_age=settings.refresh_token_expire_minutes,
    cookie_secure=settings.secure_cookie,
)

auth_backend = JWTAuthBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_active_user = fastapi_users.current_user(active=True)
optional_current_active_verified_user = fastapi_users.current_user(
    active=True, verified=True, optional=True
)
