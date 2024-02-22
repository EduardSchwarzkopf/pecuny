from datetime import datetime, timedelta, timezone


def today():
    """Get the current UTC date with time set to 00:00:00.

    Args:
        None

    Returns:
        datetime: The current UTC date.

    Raises:
        None
    """
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def get_datetime_from_timestamp(timestamp):
    """Convert a timestamp to a datetime object.

    Args:
        timestamp: The timestamp to convert.

    Returns:
        datetime: The converted datetime object.

    Raises:
        None
    """
    date = None
    try:
        # when timestamp is in seconds
        date = datetime.fromtimestamp(timestamp)
    except ValueError:
        # when timestamp is in miliseconds
        date = datetime.fromtimestamp(timestamp / 1000)

    return date


def string_to_datetime(str_date):
    """Convert a string date to a datetime object.

    Args:
        str_date: The string date to convert.

    Returns:
        datetime: The converted datetime object.

    Raises:
        ValueError: If the string date is not in the expected format.
    """
    # format: %d.%m.%Y
    return datetime.strptime(str_date, "%d.%m.%Y")


def get_last_day_of_month(dt):
    """Returns last day of month

    Args:
        dt (datetime): date to get the last day of month

    Returns:
        last_day (datetime): last day of given month
    """

    # Guaranteed to get the next month. Force any_date to 28th and then add 4 days.
    next_month = dt.replace(day=28) + timedelta(days=4)

    # Subtract all days that are over since the start of the month.
    last_day_of_month = next_month - timedelta(days=next_month.day)

    return last_day_of_month.day
