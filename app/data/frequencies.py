def get_frequency_list():
    """
    Returns a list of all available frequencies.

    Returns: A list of dictionaries representing the frequencies.
        Each dictionary contains the id and label of a frequency.
    """

    frequencies = ["once", "daily", "weekly", "monthly", "yearly"]

    return [{"id": i + 1, "label": frequencies[i]} for i in range(len(frequencies))]
