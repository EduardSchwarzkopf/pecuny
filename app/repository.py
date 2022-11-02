import uuid
from sqlalchemy import or_, extract, and_
from . import models
from .database import db
from datetime import datetime


def __str_to_class(classname: str):
    return getattr(models, classname)


def __db_action(action_name: str, object):
    method = getattr(db._session, action_name)
    method(object)


def __db_query_action(filter_option: str, name: str, attribute: str, value: str):
    class_ = __str_to_class(name)
    attr = getattr(class_, attribute)
    return getattr(db._session.query(class_), filter_option)(attr == value)


def get_all(name: str):
    class_ = __str_to_class(name)
    return db._session.query(class_).all()


def filter(name: str, attribute: str, value: str):
    return __db_query_action("filter", name, attribute, value)


def filter_by(name: str, attribute: str, value: str):
    return __db_query_action("filter_by", name, attribute, value)


async def get(name: str, id: int):
    class_ = __str_to_class(name)
    return db._session.query(class_).get(id)


def get_user(id: uuid):
    return db._session.query(models.User).get(id)


def get_transactions_from_period(
    account_id: int, start_date: datetime, end_date: datetime
):
    model_name = "Transaction"
    class_ = __str_to_class(model_name)
    attribute = getattr(class_, "account_id")

    information_class = __str_to_class(model_name + "Information")
    class_date = information_class.date

    return (
        db._session.query(class_)
        .join(class_.information)
        .filter(class_date <= end_date)
        .filter(class_date >= start_date)
        .filter(account_id == attribute)
        .all()
    )


def get_scheduled_transactions_for_date(date: datetime):
    ts = models.TransactionScheduled
    return (
        db._session.query(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end == None, ts.date_end >= date))
        .all()
    )


def save(object: models):
    if isinstance(object, list):
        return __db_action("add_all", object)

    return __db_action("add", object)


def delete(object: models):
    return __db_action("delete", object)


def refresh(object: models):
    return __db_action("refresh", object)


def refresh_all(object_list: models) -> None:
    for object in object_list:
        __db_action("refresh", object)
