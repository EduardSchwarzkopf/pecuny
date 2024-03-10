from typing import List

from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
)
from sqlalchemy import Column, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP


class Base(DeclarativeBase):
    pass


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
        """
        Adds attributes to the model instance from a dictionary.

        Args:
            self: The instance of the model.
            attribute_list (dict): A dictionary containing attribute names and values.

        Returns:
            None
        """

        model_attribute_list = self.__mapper__.attrs.keys()

        for key, value in attribute_list.items():
            if key in model_attribute_list:
                setattr(self, key, value)


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    displayname = Column(String(50))
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )


class UserId(Base):
    __abstract__ = True

    @declared_attr
    def user_id(self):
        """
        Defines a foreign key column for the user_id field.

        Args:
            self: The instance of the model.

        Returns:
            Column: The foreign key column for the user_id field.
        """

        return Column(
            UUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def user(self):
        """
        Defines a relationship to the User model.

        Args:
            self: The instance of the model.

        Returns:
            RelationshipProperty: The relationship to the User model.
        """
        return relationship("User")


class Transaction(BaseModel):
    __tablename__ = "transactions"

    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
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
        cascade="all,delete",
        lazy="selectin",
    )

    account = relationship("Account", back_populates="transactions", lazy="selectin")


class TransactionScheduled(BaseModel):
    __tablename__ = "transactions_scheduled"

    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    account = relationship(
        "Account",
        back_populates="scheduled_transactions",
        lazy="selectin",
        foreign_keys=[account_id],
    )

    information = relationship(
        "TransactionInformation",
        backref="transactions_scheduled",
        uselist=False,
        cascade="all,delete",
        lazy="selectin",
    )
    information_id = Column(Integer, ForeignKey("transactions_information.id"))
    offset_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    frequency = relationship("Frequency", cascade="all,delete", lazy="selectin")
    frequency_id = Column(Integer, ForeignKey("frequencies.id", ondelete="CASCADE"))
    date_start = Column(type_=TIMESTAMP(timezone=True))
    date_end = Column(type_=TIMESTAMP(timezone=True))


class Account(BaseModel, UserId):
    __tablename__ = "accounts"

    label = Column(String(36))
    description = Column(String(128))
    balance = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    transactions = relationship(
        "Transaction", back_populates="account", cascade="all,delete", lazy=True
    )
    scheduled_transactions = relationship(
        "TransactionScheduled",
        cascade="all,delete",
        foreign_keys=[TransactionScheduled.account_id],
        lazy=True,
    )


class TransactionInformation(BaseModel):
    __tablename__ = "transactions_information"

    amount = Column(
        Numeric(10, 2, asdecimal=False, decimal_return_scale=None), default=0
    )
    reference = Column(String(128))
    date = Column(type_=TIMESTAMP(timezone=True), default=text("now()"))
    category = relationship("TransactionCategory", lazy="selectin")
    category_id = Column(Integer, ForeignKey("transactions_category.id"))


class Frequency(BaseModel):
    __tablename__ = "frequencies"

    label = Column(String(36))


class TransactionSection(BaseModel):
    __tablename__ = "transactions_section"

    label = Column(String(36))


class TransactionCategory(BaseModel):
    __tablename__ = "transactions_category"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    user = relationship(
        "User",
        lazy="selectin",
    )

    label = Column(String(36))
    section = relationship("TransactionSection", lazy="selectin")
    section_id = Column(Integer, ForeignKey("transactions_section.id"))
