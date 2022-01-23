from fastapi import Depends
from sqlalchemy.orm import Session
from . import database


def transaction(
    handler: function, *args: dict, db: Session = Depends(database.get_db)
) -> dict:
    try:
        result = handler(*args)
        db.commit()

    except Exception as e:
        result = {}
        db.rollback()
    finally:
        return result
