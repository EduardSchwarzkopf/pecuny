from .. import models, schemas, utils, repository as repo


def get_user_by_email(email):
    return repo.filter("User", "email", email.lower()).first()


def get_user_by_username(username):
    return repo.filter("User", "username", username.lower()).first()


def auth_user(user_credentials):
    username = user_credentials.username
    user = get_user_by_email(username)
    if not user:
        user = get_user_by_username(username)

    if not user or not utils.verify(user_credentials.password, user.password):
        return None

    return user


def create_user(user: schemas.UserCreate):

    user.password = utils.hash(user.password)
    new_user = models.User(**user.dict())

    repo.save(new_user)

    return new_user


def update_user(user: schemas.UserData):
    pass


def delete_user(user_id: int):
    pass
