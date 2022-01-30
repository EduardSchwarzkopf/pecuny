from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def update_model_object(model: models, schema: schemas):
    for key, value in schema.dict().items():
        # skip empty values or same as previous
        if not value or value == getattr(model, key):
            continue

        if key == "password":
            value = hash(value)

        setattr(model, key, value)

    return model
