from sqlalchemy import or_, update as sql_update
from sqlalchemy.future import select
from . import models
from datetime import datetime
from app.database import db


async def get_all(cls: models):
    q = select(cls)
    result = await db.session.execute(q)
    result.unique()
    return result.scalars().all()


async def filter_by(cls: models, attribute: str, value: str):
    query = select(cls).where(getattr(cls, attribute) == value)
    result = await db.session.execute(query)
    return result.scalars().all()


async def get(cls: models, id: int) -> models:
    return await db.session.get(cls, id)


async def get_scheduled_transactions_from_period(
    account_id: int,
    start_date: datetime,
    end_date: datetime,
):

    transaction = models.TransactionScheduled

    query = (
        select(transaction)
        .filter(transaction.date_end <= end_date)
        .filter(transaction.date_start >= start_date)
        .filter(account_id == transaction.account_id)
    )

    result = await db.session.execute(query)
    return result.scalars().all()


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


async def get_scheduled_transactions_for_date(date: datetime):
    ts = models.TransactionScheduled
    query = (
        select(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end is None, ts.date_end >= date))
    )

    result = await db.session.execute(query)

    return result.scalars().all()


async def save(obj):
    if isinstance(obj, list):
        db.session.add_all(obj)
        return

    db.session.add(obj)


async def get_session():
    return db.session


async def commit(session):
    await session.commit()


async def update(cls: models, id: int, **kwargs):
    query = (
        sql_update(cls)
        .where(cls.id == id)
        .values(**kwargs)
        .execution_options(synchronize_session="fetch")
    )
    await db.session.execute(query)


async def delete(obj: models) -> None:
    await db.session.delete(obj)


async def refresh(obj: models):
    return await db.session.refresh(obj)


async def refresh_all(object_list: models) -> None:
    for obj in object_list:
        await db.session.refresh(obj)
