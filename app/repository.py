from sqlalchemy import or_, update as sql_update
from sqlalchemy.future import select
from . import models
from datetime import datetime
from app.database import db
from sqlalchemy.orm import selectinload, joinedload
from typing import Type, List, TypeVar
from app.models import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


ModelType = TypeVar("ModelType", bound=BaseModel)


async def get_all(cls: Type[ModelType]) -> List[ModelType]:
    q = select(cls)
    result = await db.session.execute(q)
    result.unique()
    return result.scalars().all()


async def filter_by(
    cls: Type[ModelType], attribute: str, value: str
) -> List[ModelType]:
    query = select(cls).where(getattr(cls, attribute) == value)
    result = await db.session.execute(query)
    return result.scalars().all()


async def get(cls: Type[ModelType], id: int, load_relationships=None) -> ModelType:
    stmt = select(cls).where(cls.id == id)
    if load_relationships:
        options = [selectinload(rel) for rel in load_relationships]
        stmt = stmt.options(*options)
    result = await db.session.execute(stmt)
    return result.scalars().first()


async def get_scheduled_transactions_from_period(
    account_id: int,
    start_date: datetime,
    end_date: datetime,
) -> List[models.TransactionScheduled]:
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
) -> List[models.Transaction]:
    transaction = models.Transaction
    information = models.TransactionInformation
    class_date = information.date

    query = (
        select(transaction)
        .options(joinedload(transaction.offset_transaction))
        .join(transaction.information)
        .filter(class_date <= end_date)
        .filter(class_date >= start_date)
        .filter(account_id == transaction.account_id)
    )

    result = await db.session.execute(query)
    return result.scalars().all()


async def get_scheduled_transactions_for_date(
    date: datetime,
) -> List[models.TransactionScheduled]:
    ts = models.TransactionScheduled
    query = (
        select(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end is None, ts.date_end >= date))
    )

    result = await db.session.execute(query)

    return result.scalars().all()


async def save(obj: Type[ModelType]) -> None:
    if isinstance(obj, list):
        db.session.add_all(obj)
        return

    db.session.add(obj)


async def get_session() -> AsyncSession:
    return db.session


async def commit(session) -> None:
    await session.commit()


async def update(cls: Type[ModelType], id: int, **kwargs) -> None:
    query = (
        sql_update(cls)
        .where(cls.id == id)
        .values(**kwargs)
        .execution_options(synchronize_session="fetch")
    )
    await db.session.execute(query)


async def delete(obj: Type[ModelType]) -> None:
    await db.session.delete(obj)


async def refresh(obj: Type[ModelType]) -> None:
    return await db.session.refresh(obj)


async def refresh_all(object_list: Type[ModelType]) -> None:
    for obj in object_list:
        await db.session.refresh(obj)
