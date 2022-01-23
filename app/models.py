from sqlalchemy import Column, Integer, String, Numeric, DateTime, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class UserId(Base):
    __abstract__ = True

    user_id = Column(Integer, ForeignKey("user.id"))


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(64), nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    last_seen = Column(DateTime, default=text("now()"))


class Account(BaseModel):
    __tablename__ = "account"

    label = Column(String(36))
    description = Column(String(128))
    balance = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    transactions = relationship("Transaction", cascade="all,delete", lazy=True)
    transactions_scheduled = relationship(
        "TransactionScheduled", cascade="all,delete", lazy=True
    )


class Transaction(BaseModel):
    __tablename__ = "transaction"

    account_id = Column(Integer, ForeignKey("account.id"))
    information_id = Column(Integer, ForeignKey("transaction_information.id"))
    information = relationship(
        "TransactionInformation",
        backref="transaction",
        uselist=False,
        cascade="all,delete",
        foreign_keys=[information_id],
    )

    offset_transaction_id = Column(
        Integer, ForeignKey("transaction.id", use_alter=True), nullable=True
    )
    offset_transaction = relationship(
        "Transaction",
        primaryjoin=("transaction.c.id==transaction.c.offset_transaction_id"),
        remote_side="Transaction.id",
        foreign_keys=[offset_transaction_id],
        post_update=True,
    )


class TransactionScheduled(BaseModel):
    __tablename__ = "transaction_scheduled"

    account_id = Column(Integer, ForeignKey("account.id"))
    information = relationship(
        "TransactionInformation",
        backref="transaction_scheduled",
        uselist=False,
        cascade="all,delete",
    )
    information_id = Column(Integer, ForeignKey("transaction_information.id"))

    frequency = relationship("Frequency")
    frequency_id = Column(Integer, ForeignKey("frequency.id"))
    interval = Column(Integer, default=1)
    date_start = Column(DateTime)
    date_end = Column(DateTime)


class TransactionInformation(BaseModel):
    __tablename__ = "transaction_information"

    amount = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    reference = Column(String(128))
    date = Column(DateTime, default=text("now()"))
    subcategory = relationship("TransactionSubcategory")
    subcategory_id = Column(Integer, ForeignKey("transaction_subcategory.id"))


class Frequency(BaseModel):
    __tablename__ = "frequency"

    name = Column(String(36))
    label = Column(String(36))


class TransactionCategory(BaseModel):
    __tablename__ = "transaction_category"

    label = Column(String(36))
    subcategories = relationship("TransactionSubcategory", lazy="dynamic")


class TransactionSubcategory(BaseModel):
    __tablename__ = "transaction_subcategory"

    label = Column(String(36))
    parent_category = relationship("TransactionCategory")
    parent_category_id = Column(Integer, ForeignKey("transaction_category.id"))
