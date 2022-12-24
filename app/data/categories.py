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


def get_category_list():
    income_cats = [
        {"label": "Salary", "section_id": INCOME_ID},
        {"label": "Support", "section_id": INCOME_ID},
        {"label": "Other income", "section_id": INCOME_ID},
    ]

    housing_cats = [
        {"label": "Rent", "section_id": HOUSING_ID},
        {"label": "Heating", "section_id": HOUSING_ID},
        {"label": "Electricity", "section_id": HOUSING_ID},
        {"label": "Water", "section_id": HOUSING_ID},
        {
            "label": "Renovation/Repair",
            "section_id": HOUSING_ID,
        },
        {
            "label": "TV licence",
            "section_id": HOUSING_ID,
        },  # de: GEZ
        {
            "label": "Phone and internet",
            "section_id": HOUSING_ID,
        },
        {"label": "Furniture", "section_id": HOUSING_ID},
        {
            "label": "Electric appliances",
            "section_id": HOUSING_ID,
        },
    ]

    houshold_cats = [
        {"label": "Detergent", "section_id": HOUSHOLD_ID},
        {"label": "Groceries", "section_id": HOUSHOLD_ID},
        {"label": "Beverages", "section_id": HOUSHOLD_ID},
        {
            "label": "Drink and tobacco",
            "section_id": HOUSHOLD_ID,
        },  # de Genussmittell
        {"label": "Medication", "section_id": HOUSHOLD_ID},
        {
            "label": "Hygiene products",
            "section_id": HOUSHOLD_ID,
        },
    ]

    leisure_cats = [
        {"label": "Restaurant", "section_id": LEISURE_ID},
        {"label": "Hobby", "section_id": LEISURE_ID},
        {"label": "Gym", "section_id": LEISURE_ID},
        {"label": "Pets", "section_id": LEISURE_ID},
        {
            "label": "Membership contribution",
            "section_id": LEISURE_ID,
        },  # de: Vereinsbeiträge
        {"label": "Gaming", "section_id": LEISURE_ID},
        {"label": "Vacation", "section_id": LEISURE_ID},
        {"label": "Trips", "section_id": LEISURE_ID},
        {"label": "Hairdresser", "section_id": LEISURE_ID},
        {"label": "Cosmetic", "section_id": LEISURE_ID},
        {"label": "Clothing", "section_id": LEISURE_ID},
        {
            "label": "Magazines and books",
            "section_id": LEISURE_ID,
        },
    ]

    work_cats = [
        {"label": "Furniture", "section_id": WORK_ID},
        {
            "label": "Work materials",
            "section_id": WORK_ID,
        },  # de: Arbeitsutensilien
        {"label": "Mailings", "section_id": WORK_ID},
        {"label": "Workwear", "section_id": WORK_ID},
        {"label": "Travel expenses", "section_id": WORK_ID},
    ]

    transport_cats = [
        {
            "label": "Public transport",
            "section_id": TRANSPORT_ID,
        },
        {
            "label": "Gas",
            "section_id": TRANSPORT_ID,
        },  # de: Tanken
        {
            "label": "Car repairs",
            "section_id": TRANSPORT_ID,
        },
        {"label": "Car care", "section_id": TRANSPORT_ID},
        {
            "label": "Vehicle tax",
            "section_id": TRANSPORT_ID,
        },  # de: KFZ-Steuer
    ]

    education_cats = [
        {
            "label": "Semester fees",
            "section_id": EDUCATION_ID,
        },
        {
            "label": "school fees",
            "section_id": EDUCATION_ID,
        },
        {
            "label": "Travel expenses",
            "section_id": EDUCATION_ID,
        },
        {
            "label": "Teaching aids",
            "section_id": EDUCATION_ID,
        },
        {
            "label": "Course fees",
            "section_id": EDUCATION_ID,
        },
    ]

    insurance_cats = [
        {
            "label": "Pension insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Health insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Liability insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Car insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Occupational disability insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Accident insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Term life insurance",
            "section_id": INSURANCE_ID,
        },  # de: Risikolebensversicherung
        {
            "label": "Home insurance",
            "section_id": INSURANCE_ID,
        },
        {
            "label": "Life insurance",
            "section_id": INSURANCE_ID,
        },
    ]

    finance_cats = [
        {"label": "Loans", "section_id": FINANCE_ID},
        {"label": "Pocket Money", "section_id": FINANCE_ID},
        {"label": "Alimony", "section_id": FINANCE_ID},
        {"label": "Reserves", "section_id": FINANCE_ID},
    ]

    other_cats = [
        {
            "label": "Medical Expenses",
            "section_id": OTHER_ID,
        },
        {"label": "Bank Fees", "section_id": OTHER_ID},
        {
            "label": "Tax consultancy",
            "section_id": OTHER_ID,
        },
        {"label": "Tax", "section_id": OTHER_ID},
    ]

    return (
        income_cats
        + houshold_cats
        + housing_cats
        + finance_cats
        + other_cats
        + insurance_cats
        + education_cats
        + work_cats
        + leisure_cats
        + transport_cats
    )


def get_section_list():
    return [
        {"id": INCOME_ID, "label": "Income"},
        {"id": WORK_ID, "label": "Work"},
        {"id": HOUSING_ID, "label": "Housing"},
        {"id": HOUSHOLD_ID, "label": "Houshold"},
        {"id": INSURANCE_ID, "label": "Insurance"},
        {"id": TRANSPORT_ID, "label": "Transport"},
        {"id": FINANCE_ID, "label": "Financing"},
        {"id": EDUCATION_ID, "label": "Education"},
        {"id": LEISURE_ID, "label": "Leisure"},
        {"id": OTHER_ID, "label": "Others"},
    ]
