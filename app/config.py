from pydantic import BaseSettings

# Set all required env variables here
class Settings(BaseSettings):
    enviroment: str = "dev"
    db_host: str
    db_name: str
    db_url: str = ""
    db_port: str
    db_password: str
    db_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30
    test_db_port: str
    test_db_url: str = ""


settings = Settings(".env")

setattr(
    settings,
    "db_url",
    f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
)


setattr(
    settings,
    "test_db_url",
    f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.test_db_port}/{settings.db_name}_test",
)
