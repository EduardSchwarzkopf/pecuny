import random


def generate_displayname() -> str:
    """Generate a random display name.

    Args:
        None

    Returns:
        str: The generated display name.

    Raises:
        None
    """
    adjective_list = [
        "Mighty",
        "Powerful",
        "Wise",
        "Bold",
        "Radiant",
        "Ancient",
        "Daring",
        "Valiant",
        "Brave",
        "Clever",
        "Fabled",
        "Gallant",
        "Honorable",
        "Ingenious",
        "Jolly",
        "Keen",
        "Legendary",
        "Majestic",
        "Noble",
        "Optimistic",
        "Perceptive",
        "Quick",
        "Royal",
        "Steadfast",
        "Trustworthy",
        "Unyielding",
        "Valorous",
        "Witty",
        "Exceptional",
        "Yearning",
        "Zealous",
        "Astonishing",
        "Breathtaking",
        "Charming",
        "Dazzling",
        "Elegant",
        "Fierce",
        "Gracious",
        "Humorous",
        "Incredible",
        "Joyful",
        "Knowledgeable",
        "Luminous",
        "Mystical",
        "Nurturing",
        "Outstanding",
        "Passionate",
        "Remarkable",
        "Spectacular",
        "Terrific",
        "Unforgettable",
        "Visionary",
        "Wondrous",
        "Exhilarating",
        "Youthful",
        "Zestful",
    ]
    name_list = [
        "Apple",
        "Banana",
        "Cherry",
        "Date",
        "Elderberry",
        "Fig",
        "Grape",
        "Honeydew",
        "IndianJujube",
        "Jackfruit",
        "Kiwi",
        "Lemon",
        "Mango",
        "Nectarine",
        "Orange",
        "Pineapple",
        "Raspberry",
        "Strawberry",
        "Tangerine",
        "Watermelon",
        "Passionfruit",
        "Zucchini",
        "Artichoke",
        "Broccoli",
        "Carrot",
        "Daikon",
        "Eggplant",
        "Fennel",
        "Garlic",
        "Horseradish",
        "IcePlant",
        "Jalapeno",
        "Kale",
        "Leek",
        "Mushroom",
        "Nopal",
        "Onion",
        "Pepper",
        "Quinoa",
        "Radish",
        "Spinach",
        "Tomato",
        "Zucchini",
    ]

    adjective = random.choice(adjective_list)
    name = random.choice(name_list)

    return f"{adjective}{name}"
