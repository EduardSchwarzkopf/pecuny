from fastapi_sqlalchemy import db


def transaction(handler, *args: dict) -> dict:
    try:
        result = handler(*args)
        db.session.commit()
        db.session.refresh(result)

    except Exception as e:
        result = {}
        db.session.rollback()
    finally:
        return result
