from .. import models, schemas, utils, repository as repo


def create_user(user: schemas.UserCreate):

    user.password = utils.hash(user.password)
    new_user = models.User(**user.dict())

    repo.save(new_user)

    return new_user


def update_user(user: schemas.UserData):
    pass


def delete_user(user_id: int):
    pass
