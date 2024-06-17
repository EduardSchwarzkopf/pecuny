from app.utils.enums import Frequency as frq


def get_frequency_list():
    """
    Returns a list of all available frequencies.

    Returns: A list of dictionaries representing the frequencies.
        Each dictionary contains the id and label of a frequency.
    """

    frequencies = {
        frq.ONCE.name: frq.ONCE.value,
        frq.DAILY.name: frq.DAILY.value,
        frq.WEEKLY.name: frq.WEEKLY.value,
        frq.MONTHLY.name: frq.MONTHLY.value,
        frq.YEARLY.name: frq.YEARLY.value,
    }
    return [{"id": value, "label": key} for key, value in frequencies.items()]
