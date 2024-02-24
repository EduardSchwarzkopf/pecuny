from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.database import db

from . import models, schemas
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# openssl rand -hex 32
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    """
    Creates an access token based on the provided data.

    Args:
        data (dict): The data to encode into the token.

    Returns:
        str: The access token.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire

    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def verify_access_token(token: str, credentials_exception) -> schemas.TokenData:
    """
    Verifies the access token and returns the token data.

    Args:
        token (str): The access token.
        credentials_exception: The exception to raise if the token is invalid.

    Returns:
        TokenData: The token data.

    Raises:
        HTTPException: If the token is invalid.
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)

        string_id = payload.get("sub")
        if string_id is None:
            raise credentials_exception

        token_data = schemas.TokenData(id=string_id)
    except JWTError as e:
        raise credentials_exception from e

    return token_data


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Gets the current user based on the provided access token.

    Args:
        token (str, optional): The access token. Defaults to Depends(oauth2_scheme).

    Returns:
        User: The current user.

    Raises:
        HTTPException: If no valid credentials are provided.
    """

    credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "No valid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = verify_access_token(token, credentials_exception)
    return db.session.query(models.User).get(token.id)
