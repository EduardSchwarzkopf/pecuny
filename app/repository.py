import uuid
from sqlalchemy import or_, update as sql_update
from sqlalchemy.future import select
from . import models
from .database import db
from datetime import datetime


async def get_all(cls: models):
    q = select(cls)
    result = await db._session.execute(q)
    return result.all()


async def filter_by(cls: models, attribute: str, value: str):
    query = select(cls).where(getattr(cls, attribute) == value)
    result = await db._session.execute(query)
    return result.scalars().all()


async def get(cls: models, id: int):
    query = select(cls).where(cls.id == id)
    result = await db._session.execute(query)
    db_object = result.scalar_one_or_none()
    return db_object


async def get_user(id: uuid):
    query = select(models.User).where(models.User == id)
    result = await db._session.execute(query)
    return result.scalar_one_or_none()


# TODO: update to async sessions
async def get_transactions_from_period(
    account_id: int, start_date: datetime, end_date: datetime
):
    transaction = models.Transaction
    information = models.TransactionInformation
    class_date = information.date

    return (
        db._session.query(transaction)
        .join(transaction.information)
        .filter(class_date <= end_date)
        .filter(class_date >= start_date)
        .filter(account_id == transaction.account_id)
        .all()
    )


# TODO: update to async sessions
async def get_scheduled_transactions_for_date(date: datetime):
    ts = models.TransactionScheduled
    return (
        db._session.query(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end == None, ts.date_end >= date))
        .all()
    )


async def save(obj: models):
    if isinstance(obj, list):
        db._session.add_all(obj)

    db._session.add(obj)


async def update(cls: models, id: int, **kwargs):
    query = (
        sql_update(cls)
        .where(cls.id == id)
        .values(**kwargs)
        .execution_options(synchronize_session="fetch")
    )
    await db._session.execute(query)


async def delete(obj: models) -> None:
    await db._session.delete(obj)


async def refresh(obj: models):
    print("\033[2;31;43m refresh method called, check for odd behaviour \033[0;0m")
    return db._session.refresh(obj)


async def refresh_all(object_list: models) -> None:
    print("\033[2;31;43m refresh_all method called, check for odd behaviour \033[0;0m")
    for obj in object_list:
        db._session.refresh(obj)
