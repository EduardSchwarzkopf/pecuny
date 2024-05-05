from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "pecuny"
    max_allowed_accounts: int = 5
    environment: str = "dev"
    is_testing_environment: bool = False
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
    secure_cookie: bool = True

    test_db_host: str = "test_db"
    test_db_name: str = "test_db"
    test_db_port: int = 5433
    test_db_url: str = ""

    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int | str = 465
    mail_server: str

    celery_broker_url: str = "redis://redis:6379/0"

    def __init__(self, **values):
        super().__init__(**values)
        self.configure_settings()

    def configure_settings(self):
        """
        Configures the settings for the application.

        Args:
            self: The instance of the settings to be configured.

        Returns:
            None
        """

        self.db_url = (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

        self.test_db_url = (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
            f"{self.test_db_host}:{self.test_db_port}/{self.test_db_name}"
        )

        self.access_token_expire_minutes *= 60
        self.refresh_token_expire_minutes *= 60
        self.secure_cookie = self.environment == "prod"


@lru_cache
def get_settings():
    """
    Returns the application settings.

    Returns:
        Settings: The application settings.
    """

    return Settings()


settings = get_settings()
