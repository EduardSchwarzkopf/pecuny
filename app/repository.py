from sqlalchemy import or_, update as sql_update
from sqlalchemy.future import select
from . import models
from datetime import datetime
from fastapi_async_sqlalchemy import db


def db_session(func):
    async def wrapper(*args, **kwargs):
        async with db():
            return await func(*args, **kwargs)

    return wrapper


@db_session
async def get_all(cls: models):
    q = select(cls)
    result = await db.session.execute(q)
    return result.scalars().all()


@db_session
async def filter_by(cls: models, attribute: str, value: str):
    query = select(cls).where(getattr(cls, attribute) == value)
    result = await db.session.execute(query)
    return result.scalars().all()


@db_session
async def get(cls: models, id: int):
    query = select(cls).where(cls.id == id)
    result = await db.session.execute(query)
    db_object = result.scalar()
    return db_object


@db_session
async def get_transactions_from_period(
    account_id: int, start_date: datetime, end_date: datetime
):
    transaction = models.Transaction
    information = models.TransactionInformation
    class_date = information.date

    query = (
        select(transaction)
        .join(transaction.information)
        .filter(class_date <= end_date)
        .filter(class_date >= start_date)
        .filter(account_id == transaction.account_id)
    )

    result = await db.session.execute(query)
    return result.scalars().all()


@db_session
async def get_scheduled_transactions_for_date(date: datetime):
    ts = models.TransactionScheduled
    query = (
        select(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end == None, ts.date_end >= date))
    )

    result = await db.session.execute(query)

    return result.scalars().all()


@db_session
async def save(obj):
    if isinstance(obj, list):
        db.session.add_all(obj)
        return

    db.session.add(obj)


@db_session
async def get_session():
    return db.session


async def commit(session):
    await session.commit()


@db_session
async def update(cls: models, id: int, **kwargs):
    query = (
        sql_update(cls)
        .where(cls.id == id)
        .values(**kwargs)
        .execution_options(synchronize_session="fetch")
    )
    await db.session.execute(query)


@db_session
async def delete(obj: models) -> None:
    await db.session.delete(obj)


@db_session
async def refresh(obj: models):
    print("\033[2;31;43m refresh method called, check for odd behaviour \033[0;0m")
    return db.session.refresh(obj)


@db_session
async def refresh_all(object_list: models) -> None:
    print("\033[2;31;43m refresh_all method called, check for odd behaviour \033[0;0m")
    for obj in object_list:
        db.session.refresh(obj)
