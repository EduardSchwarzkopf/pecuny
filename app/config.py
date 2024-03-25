from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "pecuny"
    max_allowed_accounts: int = 5
    enviroment: str = "dev"
    domain: str
    db_host: str
    db_name: str
    db_url: str = ""
    db_port: str
    db_password: str
    db_user: str

    refresh_token_name: str = "refresh_token"
    access_token_name: str = "access_token"
    verify_token_secret_key: str
    access_token_secret_key: str
    refresh_token_secret_key: str
    session_secret_key: str
    csrf_secret: str
    algorithm: str = "HS256"
    token_audience: List[str] = ["fastapi-users:auth"]
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1440

    test_db_name: str = "test_db"
    test_db_port: int = 5433
    test_db_url: str = ""

    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int = 465
    mail_server: str


# TODO: add lru_cache: https://fastapi.tiangolo.com/advanced/settings/ # pylint : disable=fixme
settings = Settings()

setattr(
    settings,
    "db_url",
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@"
    f"{settings.db_host}:{settings.db_port}/{settings.db_name}",
)


setattr(
    settings,
    "test_db_url",
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@"
    f"{settings.db_host}:{settings.test_db_port}/{settings.test_db_name}",
)
