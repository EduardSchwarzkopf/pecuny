from datetime import datetime
from typing import List, Type, TypeVar

from sqlalchemy import text
from sqlalchemy import update as sql_update
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from app.database import db
from app.models import BaseModel
from app.utils.enums import DatabaseFilterOperator

from . import models

# from sqlalchemy.orm.attributes import InstrumentedAttribute


ModelT = TypeVar("ModelT", bound=BaseModel)


async def get_all(cls: Type[ModelT]) -> List[ModelT]:
    """Retrieve all instances of the specified model from the database.

    Args:
        cls: The type of the model.

    Returns:
        List[ModelT]: A list of instances of the specified model.

    Raises:
        None
    """
    q = select(cls)
    result = await db.session.execute(q)
    result.unique()
    return result.scalars().all()


# TODO: Make use of InstrumentetAttribute to get rid of attributes via str
async def filter_by(
    cls: Type[ModelT],
    attribute: str,
    value: str,
    operator: DatabaseFilterOperator = DatabaseFilterOperator.EQUAL,
    # attr: InstrumentedAttribute = None,
) -> List[ModelT]:
    """
    Filters the records of a given model by a specified attribute and value.

    Args:
        cls: The model class.
        attribute: The attribute to filter by.
        value: The value to filter with.
        operator: The operator to use for the filter (default: EQUAL).

    Returns:
        List[ModelT]: The filtered records.

    Raises:
        None
    """
    # if attr:
    #     attr_name = attr.key

    condition = text(f"{attribute} {operator.value} :val")

    query = select(cls).where(condition).params(val=value)

    result = await db.session.execute(query)

    return result.unique().scalars().all()


async def get(cls: Type[ModelT], instance_id: int, load_relationships=None) -> ModelT:
    """Retrieve an instance of the specified model by its ID.

    Args:
        cls: The type of the model.
        instance_id: The ID of the instance to retrieve.
        load_relationships: Optional list of relationships to load.

    Returns:
        ModelT: The instance of the specified model with the given ID.

    Raises:
        None
    """
    stmt = select(cls).where(cls.id == instance_id)
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
    """Retrieve scheduled transactions for a specific account within a given period.

    Args:
        account_id: The ID of the account.
        start_date: The start date of the period.
        end_date: The end date of the period.

    Returns:
        List[models.TransactionScheduled]:
            A list of scheduled transactions within the specified period.

    Raises:
        None
    """
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
    """Retrieve transactions for a specific account within a given period.

    Args:
        account_id: The ID of the account.
        start_date: The start date of the period.
        end_date: The end date of the period.

    Returns:
        List[models.Transaction]: A list of transactions within the specified period.

    Raises:
        None
    """
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


async def save(obj: Type[ModelT]) -> None:
    """Save an object or a list of objects to the database.

    Args:
        obj: The object or list of objects to save.

    Returns:
        None

    Raises:
        None
    """
    if isinstance(obj, list):
        db.session.add_all(obj)
        return

    db.session.add(obj)


async def commit(session) -> None:
    """Commit the changes made in the session to the database.

    Args:
        session: The database session.

    Returns:
        None

    Raises:
        None
    """
    await session.commit()


async def update(cls: Type[ModelT], instance_id: int, **kwargs) -> None:
    """Update an instance of the specified model with the given ID.

    Args:
        cls: The type of the model.
        instance_id: The ID of the instance to update.
        **kwargs: The attributes and values to update.

    Returns:
        None

    Raises:
        None
    """
    query = (
        sql_update(cls)
        .where(cls.id == instance_id)
        .values(**kwargs)
        .execution_options(synchronize_session="fetch")
    )
    await db.session.execute(query)


async def delete(obj: Type[ModelT]) -> None:
    """Delete an object from the database.

    Args:
        obj: The object to delete.

    Returns:
        None

    Raises:
        None
    """

    # TODO: Test this
    # if isinstance(obj, list):
    #     for object in obj:
    #         db.session.delete(object)
    #     return

    # TODO: Await needed?
    await db.session.delete(obj)


async def refresh(obj: Type[ModelT]) -> None:
    """Refresh the state of an object from the database.

    Args:
        obj: The object to refresh.

    Returns:
        None

    Raises:
        None
    """
    return await db.session.refresh(obj)


async def refresh_all(object_list: Type[ModelT]) -> None:
    """Refresh the state of multiple objects from the database.

    Args:
        object_list: The list of objects to refresh.

    Returns:
        None

    Raises:
        None
    """
    for obj in object_list:
        await db.session.refresh(obj)
