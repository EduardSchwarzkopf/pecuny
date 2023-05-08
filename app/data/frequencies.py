def get_frequency_list():
    frequencies = ["once", "daily", "weekly", "monthly", "yearly"]

    return [{"id": i + 1, "label": frequencies[i]} for i in range(len(frequencies))]
