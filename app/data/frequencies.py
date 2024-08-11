from app.utils.enums import Frequency


def get_frequency_list():
    """
    Returns a list of all available frequencies.

    Returns: A list of dictionaries representing the frequencies.
        Each dictionary contains the id and label of a frequency.
    """

    return [
        {"id": frequency.value, "label": str(frequency.name).lower}
        for frequency in Frequency.get_list()
    ]
