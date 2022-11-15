from sqlalchemy import Column, Integer, String, Numeric, text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr
from .database import (
    Base,
    User,  # import User here, to be consistent with model imports
)
from sqlalchemy.dialects.postgresql import UUID


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    def add_attributes_from_dict(self, attribute_list: dict) -> None:
        model_attribute_list = self.__mapper__.attrs.keys()

        for key, value in attribute_list.items():

            if key in model_attribute_list:
                setattr(self, key, value)


class UserId(Base):
    __abstract__ = True

    @declared_attr
    def user_id(self):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def user(self):
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


class Transaction(BaseModel):
    __tablename__ = "transactions"

    account_id = Column(Integer, ForeignKey("accounts.id"))
    information_id = Column(Integer, ForeignKey("transactions_information.id"))
    information = relationship(
        "TransactionInformation",
        backref="transactions",
        uselist=False,
        cascade="all,delete",
        foreign_keys=[information_id],
        lazy="selectin",
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
        lazy="selectin",
    )


class TransactionScheduled(BaseModel):
    __tablename__ = "transactions_scheduled"

    account_id = Column(Integer, ForeignKey("accounts.id"))
    information = relationship(
        "TransactionInformation",
        backref="transactions_scheduled",
        uselist=False,
        cascade="all,delete",
        lazy="selectin",
    )
    information_id = Column(Integer, ForeignKey("transactions_information.id"))

    frequency = relationship("Frequency", cascade="all,delete", lazy="selectin")
    frequency_id = Column(Integer, ForeignKey("frequencies.id", ondelete="CASCADE"))
    interval = Column(Integer, default=1)
    date_start = Column(type_=TIMESTAMP(timezone=True))
    date_end = Column(type_=TIMESTAMP(timezone=True))


class TransactionInformation(BaseModel):
    __tablename__ = "transactions_information"

    amount = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    reference = Column(String(128))
    date = Column(type_=TIMESTAMP(timezone=True), default=text("now()"))
    subcategory = relationship("TransactionSubcategory", lazy="selectin")
    subcategory_id = Column(Integer, ForeignKey("transactions_subcategories.id"))


class Frequency(BaseModel):
    __tablename__ = "frequencies"

    name = Column(String(36))
    label = Column(String(36))


class TransactionCategory(BaseModel):
    __tablename__ = "transactions_categories"

    label = Column(String(36))
    subcategories = relationship(
        "TransactionSubcategory", lazy="selectin", backref="transactions_categories"
    )


class TransactionSubcategory(BaseModel):
    __tablename__ = "transactions_subcategories"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    user = relationship(
        "User",
        lazy="selectin",
    )

    label = Column(String(36))
    is_income = Column(Boolean, default=False)
    parent_category_id = Column(Integer, ForeignKey("transactions_categories.id"))
