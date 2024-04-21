import contextlib
import datetime
from datetime import datetime as dt
from datetime import timedelta, timezone


def today():
    """Get the current UTC date with time set to 00:00:00.

    Args:
        None

    Returns:
        datetime: The current UTC date.

    Raises:
        None
    """
    return dt.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


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
        date = dt.fromtimestamp(timestamp)
    except ValueError:
        # when timestamp is in miliseconds
        date = dt.fromtimestamp(timestamp / 1000)

    return date


def string_to_datetime(str_date: str):
    """Convert a string date to a datetime object.

    Args:
        str_date: The string date to convert.

    Returns:
        datetime: The converted datetime object.

    Raises:
        ValueError: If the string date is not in the expected format.
    """
    with contextlib.suppress(ValueError):
        try:
            # Direct support for 'Z' and no timezone information
            return dt.fromisoformat(str_date)
        except ValueError:
            # Handling timezone offsets formatted as +HH:MM or -HH:MM
            if str_date[-3] in ["+", "-"]:
                with contextlib.suppress(ValueError):
                    return _extracted_from_string_to_datetime(str_date)

    # If ISO 8601 parsing fails, try predefined formats
    date_formats = ["%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]
    for fmt in date_formats:
        with contextlib.suppress(ValueError):
            return datetime.datetime.strptime(str_date, fmt)

    raise ValueError(f"Date format not recognized: {str_date}")


def _extracted_from_string_to_datetime(str_date: str):
    """
    Convert a string date to a datetime object adjusting for timezone.

    Args:
        str_date (str): A string representing a date with timezone information.

    Returns:
        datetime: A datetime object adjusted for the timezone specified in the input string.
    """
    # Remove the colon from the timezone part
    no_colon = str_date[:-3] + str_date[-3:].replace(":", "")
    ddt = dt.fromisoformat(no_colon)
    # Adjust if necessary based on the last part of the string for timezone
    timezone_delta = datetime.timedelta(
        hours=int(str_date[-3:-1]),
        minutes=int(str_date[-2:]) * int(f"{str_date[-3]}1"),
    )
    return ddt - timezone_delta if str_date[-3] == "+" else ddt + timezone_delta


def get_last_day_of_month(date: dt):
    """Returns last day of month

    Args:
        dt (datetime): date to get the last day of month

    Returns:
        last_day (datetime): last day of given month
    """

    # Guaranteed to get the next month. Force any_date to 28th and then add 4 days.
    next_month = date.replace(day=28) + timedelta(days=4)

    # Subtract all days that are over since the start of the month.
    last_day_of_month = next_month - timedelta(days=next_month.day)

    return last_day_of_month.day
