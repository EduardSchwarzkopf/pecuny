from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple, Type, Union

from sqlalchemy import Select, exists, func, text
from sqlalchemy import update as sql_update
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app import models
from app.database import SessionLocal
from app.exceptions.base_service_exception import EntityNotFoundException
from app.utils.enums import DatabaseFilterOperator, Frequency
from app.utils.fields import IdField
from app.utils.types import ModelT


class Repository:

    def _load_relationships(
        self, query: Select, relationships: InstrumentedAttribute = None
    ) -> Select:
        """Apply loading options for specified relationships to a query.

        Args:
            query: The SQLAlchemy query object.
            *relationships: Class-bound attributes representing relationships to load.

        Returns:
            The modified query with loading options applied.
        """
        if relationships:
            options = [selectinload(rel) for rel in relationships]
            query = query.options(*options)
        return query

    async def get_all(
        self,
        cls: Type[ModelT],
        load_relationships_list: Optional[list[InstrumentedAttribute]] = None,
    ) -> list[ModelT]:
        """Retrieve all instances of the specified model from the database.

        Args:
            cls: The type of the model.
            load_relationships: Optional list of relationships to load.

        Returns:
            list[ModelT]: A list of instances of the specified model.
        """
        q = select(cls)
        q = self._load_relationships(q, load_relationships_list)
        async with SessionLocal() as session:
            result = await session.execute(q)
        return result.unique().scalars().all()

    async def get(
        self,
        cls: Type[ModelT],
        instance_id: Union[int, IdField],
        load_relationships_list: Optional[list[InstrumentedAttribute]] = None,
    ) -> ModelT:
        """Retrieve an instance of the specified model by its ID.

        Args:
            cls: The type of the model.
            instance_id: The ID of the instance to retrieve.
            load_relationships: Optional list of relationships to load.

        Returns:
            Optional[ModelT]:
                The instance of the specified model with
                the given ID, or None if not found.
        """
        q = select(cls).where(cls.id == instance_id)
        q = self._load_relationships(q, load_relationships_list)

        async with SessionLocal() as session:
            result = await session.execute(q)

        model = result.scalars().first()

        if model is None:
            raise EntityNotFoundException(cls, instance_id)

        return model

    async def filter_by(
        self,
        cls: Type[ModelT],
        attribute: InstrumentedAttribute,
        value: Any,
        operator: DatabaseFilterOperator = DatabaseFilterOperator.EQUAL,
        load_relationships_list: Optional[list[str]] = None,
    ) -> list[ModelT]:
        """
        Filters the records of a given model by a specified attribute and value.

        Args:
            cls: The model class.
            attribute: The attribute to filter by.
            value: The value to filter with.
            operator: The operator to use for the filter (default: EQUAL).

        Returns:
            list[Type[ModelT]]: The filtered records.

        Raises:
            None
        """
        if operator == DatabaseFilterOperator.LIKE:
            condition = attribute.ilike(f"%{value}%")
        elif operator == DatabaseFilterOperator.IS_NOT:
            condition = attribute.is_not(value)
        else:
            condition = text(f"{attribute.key} {operator.value} :val")

        q = select(cls).where(condition).params(val=value)
        q = self._load_relationships(q, load_relationships_list)

        async with SessionLocal() as session:
            result = await session.execute(q)

        return result.unique().scalars().all()

    async def filter_by_multiple(
        self,
        cls: Type[ModelT],
        conditions: List[Tuple[InstrumentedAttribute, Any, DatabaseFilterOperator]],
        load_relationships_list: Optional[list[str]] = None,
    ) -> list[ModelT]:
        """
        Filters the records of a given model by multiple attributes and values.

        Args:
            cls: The model class.
            conditions: A list of tuples where each tuple contains an attribute to filter by,
                        a value to filter with, and an optional operator
                        (if not provided, EQUAL is used).
            load_relationships_list: Optional list of relationships to load.

        Returns:
            list[ModelT]: The filtered records.
        """

        where_conditions = []
        params = {}
        for i, (attribute, value, operator) in enumerate(conditions):
            param_name = f"val{i}"

            if operator == DatabaseFilterOperator.LIKE:
                condition = attribute.ilike(f"%{value}%")
            elif operator == DatabaseFilterOperator.IS_NOT:
                condition = attribute.is_not(value)
            else:
                condition = text(f"{attribute.key} {operator.value} :{param_name}")
                params[param_name] = value

            where_conditions.append(condition)

        q = select(cls)
        if where_conditions:
            for condition in where_conditions:
                q = q.where(condition)

        q = q.params(**params)
        q = self._load_relationships(q, load_relationships_list)

        async with SessionLocal() as session:
            result = await session.execute(q)

        return result.scalars().unique().all()

    async def get_scheduled_transactions_by_frequency(
        self,
        frequency_id: int,
        today: datetime,
    ) -> list[models.TransactionScheduled]:
        """
        Retrieve all scheduled transactions for a specific frequency
        that are active and not yet processed today.

        Args:
            frequency_id (int): The frequency ID to filter by.
            today (datetime): The current date to use for filtering.

        Returns:
            list[models.TransactionScheduled]: A list of scheduled transactions.
        """
        model = models.TransactionScheduled

        def get_period_start_date(frequency_id: int) -> datetime:
            match frequency_id:
                case Frequency.DAILY.value:
                    return today
                case Frequency.WEEKLY.value:
                    return today - timedelta(days=7)
                case Frequency.MONTHLY.value:
                    return today.replace(month=today.month - 1)
                case Frequency.YEARLY.value:
                    return today.replace(year=today.year - 1)
                case _:
                    raise ValueError("Invalid frequency_id")

        period_start_date = get_period_start_date(frequency_id)

        transaction_exists_condition = ~exists(
            select(models.Transaction)
            .join(models.TransactionInformation)
            .where(
                models.Transaction.scheduled_transaction_id == model.id,
                func.date(models.TransactionInformation.date) >= period_start_date,
            )
            .correlate(model)
        )

        query = select(model).where(
            model.date_start <= today,
            model.date_end >= today,
            model.is_active == True,  # pylint: disable=singleton-comparison
            model.frequency_id == frequency_id,
            transaction_exists_condition,
        )

        async with SessionLocal() as session:
            result = await session.execute(query)
        return result.scalars().all()

    async def get_transactions_from_period(
        self, wallet_id: int, start_date: datetime, end_date: datetime
    ) -> list[models.Transaction]:
        """Retrieve transactions for a specific wallet within a given period.

        Args:
            wallet_id: The ID of the wallet.
            start_date: The start date of the period.
            end_date: The end date of the period.

        Returns:
            list[models.Transaction]: A list of transactions within the specified period.

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
            .filter(wallet_id == transaction.wallet_id)
        )

        async with SessionLocal() as session:
            result = await session.execute(query)
        return result.scalars().all()

    async def save(self, obj: Union[ModelT, List[ModelT]]) -> None:
        """Save an object or a list of objects to the database.

        Args:
            obj: The object or list of objects to save.

        Returns:
            None

        Raises:
            None
        """

        async with SessionLocal() as session, session.begin():
            if isinstance(obj, list):
                session.add_all(obj)
                return

            session.add(obj)

    async def update(self, cls: Type[ModelT], instance_id: int, **kwargs):
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
        async with SessionLocal() as session:
            await session.execute(query)

    async def delete(self, obj: Type[ModelT]) -> None:
        """Delete an object from the database.

        Args:
            obj: The object to delete.

        """

        async with SessionLocal() as session, session.begin():
            await session.delete(obj)

    async def refresh(self, obj: Type[ModelT]) -> None:
        """Refresh the state of an object from the database.

        Args:
            obj: The object to refresh.

        Returns:
            None

        Raises:
            None
        """
        async with SessionLocal() as session:
            return await session.refresh(obj)

    async def refresh_all(self, object_list: List[ModelT]) -> None:
        """Refresh the state of multiple objects from the database.

        Args:
            object_list: The list of objects to refresh.

        Returns:
            None

        Raises:
            None
        """
        async with SessionLocal() as session:
            for obj in object_list:
                await session.refresh(obj)
