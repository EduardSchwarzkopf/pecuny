from typing import List
from fastapi import Depends, APIRouter, status
from .. import models, schemas, oauth2, transaction_manager as tm
from ..services import users as service


router = APIRouter(prefix="/users", tags=["Users"])
response_model = schemas.UserData


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
def create_user(
    user: schemas.UserCreate,
):
    new_user = tm.transaction(service.create_user, user)
    return new_user


@router.put("/{user_id}", response_model=response_model)
def update_user(
    user: schemas.UserData,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    user = tm.transaction(service.update_user, user)
    return user


@router.delete(
    "/{user_id}",
)
def delete_user(
    user_id: int, current_user: models.User = Depends(oauth2.get_current_user)
):
    result = tm.transaction(service.delete_user, user_id)
    return result
