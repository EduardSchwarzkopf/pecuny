from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from .. import schemas, utils, oauth2
from ..services import users

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
):
    user = users.auth_user(user_credentials)

    if not user:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    user_data = {"user_id": user.id}
    access_token = oauth2.create_access_token(data=user_data)

    return {"access_token": access_token, "token_type": "bearer"}
