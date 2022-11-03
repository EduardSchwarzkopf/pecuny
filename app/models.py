from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    text,
    Boolean,
    update as sqlalchemy_update,
    delete as sqlalchemy_delete,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr
from .database import Base, db, User
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.future import select
from typing import List
from typing_extensions import Self


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    @classmethod
    async def create(cls, **kwargs) -> Self:
        obj = cls(**kwargs)
        db._session.add(obj)
        return obj

    @classmethod
    async def update(cls, id, **kwargs) -> None:
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db._session.execute(query)

    @classmethod
    async def get(cls, id) -> Self:
        obj = await db._session.query(cls).get(id)
        return obj

    @classmethod
    async def filter(cls, attribute: str, value: str) -> List[Self]:

        query = select(cls).where(getattr(cls, attribute) == value)
        result = await db._session.execute(query)
        object_list = result.scalars().all()
        return object_list

    @classmethod
    async def delete(cls, id):
        query = sqlalchemy_delete(cls).where(cls.id == id)
        await db._session.execute(query)


class UserId(Base):
    __abstract__ = True

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def user(cls):
        return relationship("User")


class Account(BaseModel, UserId):
    __tablename__ = "accounts"

    label = Column(String(36))
    description = Column(String(128))
    balance = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    transactions = relationship("Transaction", cascade="all,delete", lazy=True)
    transactions_scheduled = relationship(
        "TransactionScheduled", cascade="all,delete", lazy=True
    )


class Transaction(BaseModel, UserId):
    __tablename__ = "transactions"

    account_id = Column(Integer, ForeignKey("accounts.id"))
    information_id = Column(Integer, ForeignKey("transactions_information.id"))
    information = relationship(
        "TransactionInformation",
        backref="transactions",
        uselist=False,
        cascade="all,delete",
        foreign_keys=[information_id],
    )

    offset_transactions_id = Column(
        Integer,
        ForeignKey(
            "transactions.id",
            use_alter=True,
            name="transactions_offset_transactions_id_fkey",
        ),
        nullable=True,
    )
    offset_transaction = relationship(
        "Transaction",
        primaryjoin=("transactions.c.id==transactions.c.offset_transactions_id"),
        remote_side="Transaction.id",
        foreign_keys=[offset_transactions_id],
        post_update=True,
    )


class TransactionScheduled(BaseModel):
    __tablename__ = "transactions_scheduled"

    account_id = Column(Integer, ForeignKey("accounts.id"))
    information = relationship(
        "TransactionInformation",
        backref="transactions_scheduled",
        uselist=False,
        cascade="all,delete",
    )
    information_id = Column(Integer, ForeignKey("transactions_information.id"))

    frequency = relationship("Frequency", cascade="all,delete")
    frequency_id = Column(Integer, ForeignKey("frequencies.id", ondelete="CASCADE"))
    interval = Column(Integer, default=1)
    date_start = Column(DateTime)
    date_end = Column(DateTime)


class TransactionInformation(BaseModel):
    __tablename__ = "transactions_information"

    amount = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    reference = Column(String(128))
    date = Column(DateTime, default=text("now()"))
    subcategory = relationship("TransactionSubcategory")
    subcategory_id = Column(Integer, ForeignKey("transactions_subcategories.id"))


class Frequency(BaseModel):
    __tablename__ = "frequencies"

    name = Column(String(36))
    label = Column(String(36))


class TransactionCategory(BaseModel):
    __tablename__ = "transactions_categories"

    label = Column(String(36))
    subcategories = relationship(
        "TransactionSubcategory", lazy="dynamic", backref="transactions_categories"
    )


class TransactionSubcategory(BaseModel):
    __tablename__ = "transactions_subcategories"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    user = relationship("User")

    label = Column(String(36))
    is_income = Column(Boolean, default=False)
    parent_category_id = Column(Integer, ForeignKey("transactions_categories.id"))
