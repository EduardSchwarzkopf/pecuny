from typing import Any
from . import models
from .database import db


async def transaction(handler, *args: Any) -> Any:
    try:
        result = await handler(*args)
        await db._session.commit()
        if _is_models_object(result):
            await db._session.refresh(result)

    except Exception as e:
        result = {}
        await db._session.rollback()
    finally:
        return result


def _is_models_object(db_object):
    return getattr(db_object, "__module__", None) == models.__name__
