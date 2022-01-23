from pydantic import BaseSettings

# Set all required env variables here
class Settings(BaseSettings):
    db_host: str
    db_name: str
    db_port: str
    db_passwort: str
    db_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30


settings = Settings(".env")
