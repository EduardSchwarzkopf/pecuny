from sqlalchemy import or_, extract
from . import models
from fastapi_sqlalchemy import db


def __str_to_class(classname):
    return getattr(models, classname)


def __db_action(action_name, object):
    method = getattr(db.session, action_name)
    method(object)


def get_all(name):
    class_ = __str_to_class(name)
    return db.session.query(class_).all()


def filter(name, attribute, value):
    class_ = __str_to_class(name)
    attr = getattr(class_, attribute)
    return db.session.query(class_).filter(attr == value)


def get(name, id):
    class_ = __str_to_class(name)
    return db.session.query(class_).get(id)


def get_from_month(name, date, attribute, value):
    class_ = __str_to_class(name)
    attribute = getattr(class_, attribute)

    information_class = __str_to_class(name + "Information")
    class_date = information_class.date
    month = extract("month", class_date)
    year = extract("year", class_date)

    return (
        db.session.query(class_)
        .join(class_.information)
        .filter(year == date.year)
        .filter(month == date.month)
        .filter(value == attribute)
        .all()
    )


def get_scheduled_transactions_for_date(date):
    ts = models.TransactionScheduled
    return (
        db.query(ts)
        .filter(ts.date_start <= date)
        .filter(or_(ts.date_end == None, ts.date_end >= date))
        .all()
    )


def save(object):
    if isinstance(object, list):
        return __db_action("add_all", object)

    return __db_action("add", object)


def delete(object):
    return __db_action("delete", object)


def refresh(object):
    return __db_action("refresh", object)
