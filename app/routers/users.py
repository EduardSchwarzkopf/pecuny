from fastapi import Depends, APIRouter, Response, status, HTTPException
from .. import models, schemas, oauth2, transaction_manager as tm
from ..services import users as service


router = APIRouter(prefix="/users", tags=["Users"])
response_model = schemas.UserData


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
def create_user(
    user: schemas.UserCreate,
):
    if service.get_user_by_email(user.email):
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="E-Mail address already in use"
        )

    if service.get_user_by_username(user.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already in use")

    return tm.transaction(service.create_user, user)


@router.put("/{user_id}", response_model=response_model)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="You are not allowed to update this user"
        )

    email_user = service.get_user_by_email(user_data.email)
    if email_user and current_user != email_user:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="E-Mail address already in use"
        )

    username_user = service.get_user_by_username(user_data.username)
    if username_user and current_user != username_user:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Username address already in use"
        )

    if user_data.password is not None and not user_data.password.strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Empty Password not allowed"
        )

    return tm.transaction(service.update_user, user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, current_user: models.User = Depends(oauth2.get_current_user)
):
    # TODO: Add more permissions later
    if current_user.id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="You are not allowed to delete this user"
        )
    tm.transaction(service.delete_user, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
