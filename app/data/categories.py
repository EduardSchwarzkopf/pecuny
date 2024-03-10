from typing import Dict, List, Union

INCOME_ID = 1
HOUSING_ID = 2
HOUSHOLD_ID = 3
LEISURE_ID = 4
WORK_ID = 5
TRANSPORT_ID = 6
EDUCATION_ID = 7
INSURANCE_ID = 8
FINANCE_ID = 9
OTHER_ID = 10
FAMILY_ID = 11
HEALTH_ID = 12


def get_category_list() -> list[dict[str, object]]:
    """
    Returns a list of all available expense categories.

    Returns:
        list[dict[str, object]]:
            A list of dictionaries representing the expense categories.
            Each dictionary contains the label and section_id of a category.
    """

    education_cats = [
        {"label": "Course fees", "section_id": EDUCATION_ID},
        {"label": "School fees", "section_id": EDUCATION_ID},
        {"label": "Semester fees", "section_id": EDUCATION_ID},
        {"label": "Teaching aids", "section_id": EDUCATION_ID},
        {"label": "Children’s Education", "section_id": EDUCATION_ID},
        {"label": "Professional Development", "section_id": EDUCATION_ID},
        {"label": "Travel Expenses (Education)", "section_id": EDUCATION_ID},
    ]

    finance_cats = [
        {"label": "Alimony", "section_id": FINANCE_ID},
        {"label": "Loans", "section_id": FINANCE_ID},
        {"label": "Pocket Money", "section_id": FINANCE_ID},
        {"label": "Reserves", "section_id": FINANCE_ID},
        {"label": "Investments", "section_id": FINANCE_ID},
        {"label": "Savings", "section_id": FINANCE_ID},
        {"label": "Retirement Savings", "section_id": FINANCE_ID},
    ]

    household_cats = [
        {"label": "Beverages", "section_id": HOUSHOLD_ID},
        {"label": "Cleaning Supplies", "section_id": HOUSHOLD_ID},
        {"label": "Detergent", "section_id": HOUSHOLD_ID},
        {"label": "Drink and Tobacco", "section_id": HOUSHOLD_ID},
        {"label": "Groceries", "section_id": HOUSHOLD_ID},
        {"label": "Hygiene products", "section_id": HOUSHOLD_ID},
        {"label": "Medication", "section_id": HOUSHOLD_ID},
        {"label": "Home Maintenance", "section_id": HOUSHOLD_ID},
    ]

    housing_cats = [
        {"label": "Electric Appliances", "section_id": HOUSING_ID},
        {"label": "Electricity", "section_id": HOUSING_ID},
        {"label": "Furniture", "section_id": HOUSING_ID},
        {"label": "Heating", "section_id": HOUSING_ID},
        {"label": "Phone and internet", "section_id": HOUSING_ID},
        {"label": "Rent", "section_id": HOUSING_ID},
        {"label": "Renovation/Repair", "section_id": HOUSING_ID},
        {"label": "TV licence", "section_id": HOUSING_ID},
        {"label": "Water", "section_id": HOUSING_ID},
    ]

    income_cats = [
        {"label": "Salary", "section_id": INCOME_ID},
        {"label": "Support", "section_id": INCOME_ID},
        {"label": "Other income", "section_id": INCOME_ID},
        {"label": "Investment Income", "section_id": INCOME_ID},
        {"label": "Rental Income", "section_id": INCOME_ID},
        {"label": "Gifts Received", "section_id": INCOME_ID},
        {"label": "Freelance / Side Hustles", "section_id": INCOME_ID},
    ]

    insurance_cats = [
        {"label": "Accident insurance", "section_id": INSURANCE_ID},
        {"label": "Car insurance", "section_id": INSURANCE_ID},
        {"label": "Health insurance", "section_id": INSURANCE_ID},
        {"label": "Home insurance", "section_id": INSURANCE_ID},
        {"label": "Liability insurance", "section_id": INSURANCE_ID},
        {"label": "Life insurance", "section_id": INSURANCE_ID},
        {"label": "Occupational disability insurance", "section_id": INSURANCE_ID},
        {"label": "Pension insurance", "section_id": INSURANCE_ID},
        {"label": "Term life insurance", "section_id": INSURANCE_ID},
    ]

    leisure_cats = [
        {"label": "Clothing", "section_id": LEISURE_ID},
        {"label": "Cosmetic", "section_id": LEISURE_ID},
        {"label": "Gaming", "section_id": LEISURE_ID},
        {"label": "Gym", "section_id": LEISURE_ID},
        {"label": "Hairdresser", "section_id": LEISURE_ID},
        {"label": "Hobby", "section_id": LEISURE_ID},
        {"label": "Magazines and Books", "section_id": LEISURE_ID},
        {"label": "Membership Contribution", "section_id": LEISURE_ID},
        {"label": "Pets", "section_id": LEISURE_ID},
        {"label": "Restaurant", "section_id": LEISURE_ID},
        {"label": "Trips", "section_id": LEISURE_ID},
        {"label": "Vacation", "section_id": LEISURE_ID},
        {"label": "Wellness", "section_id": LEISURE_ID},
        {"label": "Streaming Services", "section_id": LEISURE_ID},
        {"label": "Apps and Software", "section_id": LEISURE_ID},
    ]

    other_cats = [
        {"label": "Bank Fees", "section_id": OTHER_ID},
        {"label": "Medical Expenses", "section_id": OTHER_ID},
        {"label": "Tax", "section_id": OTHER_ID},
        {"label": "Tax consultancy", "section_id": OTHER_ID},
        {"label": "Legal Fees", "section_id": OTHER_ID},
        {"label": "Charitable Donations", "section_id": OTHER_ID},
        {"label": "Gifts Given", "section_id": OTHER_ID},
        {"label": "Holiday Expenses", "section_id": OTHER_ID},
    ]

    transport_cats = [
        {"label": "Car Care", "section_id": TRANSPORT_ID},
        {"label": "Car Repairs", "section_id": TRANSPORT_ID},
        {"label": "Gas", "section_id": TRANSPORT_ID},
        {"label": "Public Transport", "section_id": TRANSPORT_ID},
        {"label": "Vehicle Tax", "section_id": TRANSPORT_ID},
    ]

    work_cats = [
        {"label": "Furniture", "section_id": WORK_ID},
        {"label": "Mailings", "section_id": WORK_ID},
        {"label": "Travel Expenses (Work)", "section_id": WORK_ID},
        {"label": "Work Materials", "section_id": WORK_ID},
        {"label": "Workwear", "section_id": WORK_ID},
    ]

    family_cats = [
        {"label": "Child Care", "section_id": FAMILY_ID},
        {"label": "Pet Care", "section_id": FAMILY_ID},
    ]

    health_cats = [
        {"label": "Doctor Visits", "section_id": HEALTH_ID},
        {"label": "Dental Care", "section_id": HEALTH_ID},
        {"label": "Vision Care", "section_id": HEALTH_ID},
        {"label": "Personal Care", "section_id": HEALTH_ID},
    ]

    # Assemble all categories into a single list before returning
    return (
        education_cats
        + finance_cats
        + household_cats
        + housing_cats
        + income_cats
        + insurance_cats
        + leisure_cats
        + other_cats
        + transport_cats
        + work_cats
        + family_cats
        + health_cats
    )


def get_section_list() -> list[dict[str, Union[str, int]]]:
    """
    Returns a list of all available expense sections.

    Returns:
        list[dict[str, Union[str, int]]]:
            A list of dictionaries representing the expense sections.
            Each dictionary contains the id and label of a section.
    """

    return [
        {"id": INCOME_ID, "label": "Income"},
        {"id": WORK_ID, "label": "Work"},
        {"id": HOUSING_ID, "label": "Housing"},
        {"id": HOUSHOLD_ID, "label": "Household"},
        {"id": INSURANCE_ID, "label": "Insurance"},
        {"id": TRANSPORT_ID, "label": "Transport"},
        {"id": FINANCE_ID, "label": "Finance"},
        {"id": EDUCATION_ID, "label": "Education"},
        {"id": LEISURE_ID, "label": "Leisure"},
        {"id": OTHER_ID, "label": "Others"},
        {"id": FAMILY_ID, "label": "Family"},
        {"id": HEALTH_ID, "label": "Health"},
    ]
