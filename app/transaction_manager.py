from typing import Any
from fastapi_sqlalchemy import db
from . import models


def transaction(handler, *args: Any) -> Any:
    try:
        result = handler(*args)
        db.session.commit()
        if _is_models_object(result):
            db.session.refresh(result)

    except Exception as e:
        result = {}
        db.session.rollback()
    finally:
        return result


def _is_models_object(db_object):
    return getattr(db_object, "__module__", None) == models.__name__
