from pydantic import BaseSettings

# Set all required env variables here
class Settings(BaseSettings):
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


settings = Settings(".env")

setattr(
    settings,
    "db_url",
    f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
)
