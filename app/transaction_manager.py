from typing import Any
from . import models
from fastapi_async_sqlalchemy import db


async def transaction(handler, *args: Any) -> Any:
    try:
        result = await handler(*args)
        await db.session.commit()
        if _is_models_object(result):
            await db.session.refresh(result)

    except Exception as e:
        result = {}
        await db.session.rollback()
    finally:
        return result


def _is_models_object(db_object):
    return getattr(db_object, "__module__", None) == models.__name__
