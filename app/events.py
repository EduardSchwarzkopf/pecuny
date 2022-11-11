from app import models
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column
from sqlalchemy.ext.asyncio import AsyncSession


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


def _get_subcategory_list():
    income_cats = [
        {"label": "Salary", "is_income": True, "parent_category_id": INCOME_ID},
        {"label": "Support", "is_income": True, "parent_category_id": INCOME_ID},
        {"label": "Other income", "is_income": True, "parent_category_id": INCOME_ID},
    ]

    housing_cats = [
        {"label": "Rent", "is_income": False, "parent_category_id": HOUSING_ID},
        {"label": "Heating", "is_income": False, "parent_category_id": HOUSING_ID},
        {"label": "Electricity", "is_income": False, "parent_category_id": HOUSING_ID},
        {"label": "Water", "is_income": False, "parent_category_id": HOUSING_ID},
        {
            "label": "Renovation/Repair",
            "is_income": False,
            "parent_category_id": HOUSING_ID,
        },
        {
            "label": "TV licence",
            "is_income": False,
            "parent_category_id": HOUSING_ID,
        },  # de: GEZ
        {
            "label": "Phone and internet",
            "is_income": False,
            "parent_category_id": HOUSING_ID,
        },
        {"label": "Furniture", "is_income": False, "parent_category_id": HOUSING_ID},
        {
            "label": "Electric appliances",
            "is_income": False,
            "parent_category_id": HOUSING_ID,
        },
    ]

    houshold_cats = [
        {"label": "Detergent", "is_income": False, "parent_category_id": HOUSHOLD_ID},
        {"label": "Groceries", "is_income": False, "parent_category_id": HOUSHOLD_ID},
        {"label": "Beverages", "is_income": False, "parent_category_id": HOUSHOLD_ID},
        {
            "label": "Drink and tobacco",
            "is_income": False,
            "parent_category_id": HOUSHOLD_ID,
        },  # de Genussmittell
        {"label": "Medication", "is_income": False, "parent_category_id": HOUSHOLD_ID},
        {
            "label": "Hygiene products",
            "is_income": False,
            "parent_category_id": HOUSHOLD_ID,
        },
    ]

    leisure_cats = [
        {"label": "Restaurant", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Hobby", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Gym", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Pets", "is_income": False, "parent_category_id": LEISURE_ID},
        {
            "label": "Membership contribution",
            "is_income": False,
            "parent_category_id": LEISURE_ID,
        },  # de: Vereinsbeiträge
        {"label": "Gaming", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Vacation", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Trips", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Hairdresser", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Cosmetic", "is_income": False, "parent_category_id": LEISURE_ID},
        {"label": "Clothing", "is_income": False, "parent_category_id": LEISURE_ID},
        {
            "label": "Magazines and books",
            "is_income": False,
            "parent_category_id": LEISURE_ID,
        },
    ]

    work_cats = [
        {"label": "Furniture", "is_income": False, "parent_category_id": WORK_ID},
        {
            "label": "Work materials",
            "is_income": False,
            "parent_category_id": WORK_ID,
        },  # de: Arbeitsutensilien
        {"label": "Mailings", "is_income": False, "parent_category_id": WORK_ID},
        {"label": "Workwear", "is_income": False, "parent_category_id": WORK_ID},
        {"label": "Travel expenses", "is_income": False, "parent_category_id": WORK_ID},
    ]

    transport_cats = [
        {
            "label": "Public transport",
            "is_income": False,
            "parent_category_id": TRANSPORT_ID,
        },
        {
            "label": "Gas",
            "is_income": False,
            "parent_category_id": TRANSPORT_ID,
        },  # de: Tanken
        {
            "label": "Car repairs",
            "is_income": False,
            "parent_category_id": TRANSPORT_ID,
        },
        {"label": "Car care", "is_income": False, "parent_category_id": TRANSPORT_ID},
        {
            "label": "Vehicle tax",
            "is_income": False,
            "parent_category_id": TRANSPORT_ID,
        },  # de: KFZ-Steuer
    ]

    education_cats = [
        {
            "label": "Semester fees",
            "is_income": False,
            "parent_category_id": EDUCATION_ID,
        },
        {
            "label": "school fees",
            "is_income": False,
            "parent_category_id": EDUCATION_ID,
        },
        {
            "label": "Travel expenses",
            "is_income": False,
            "parent_category_id": EDUCATION_ID,
        },
        {
            "label": "Teaching aids",
            "is_income": False,
            "parent_category_id": EDUCATION_ID,
        },
        {
            "label": "Course fees",
            "is_income": False,
            "parent_category_id": EDUCATION_ID,
        },
    ]

    insurance_cats = [
        {
            "label": "Pension insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Health insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Liability insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Car insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Occupational disability insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Accident insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Term life insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },  # de: Risikolebensversicherung
        {
            "label": "Home insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
        {
            "label": "Life insurance",
            "is_income": False,
            "parent_category_id": INSURANCE_ID,
        },
    ]

    finance_cats = [
        {"label": "Loans", "is_income": False, "parent_category_id": FINANCE_ID},
        {"label": "Pocket Money", "is_income": False, "parent_category_id": FINANCE_ID},
        {"label": "Alimony", "is_income": False, "parent_category_id": FINANCE_ID},
        {"label": "Reserves", "is_income": False, "parent_category_id": FINANCE_ID},
    ]

    other_cats = [
        {
            "label": "Medical Expenses",
            "is_income": False,
            "parent_category_id": OTHER_ID,
        },
        {"label": "Bank Fees", "is_income": False, "parent_category_id": OTHER_ID},
        {
            "label": "Tax consultancy",
            "is_income": False,
            "parent_category_id": OTHER_ID,
        },
        {"label": "Tax", "is_income": False, "parent_category_id": OTHER_ID},
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


def _get_category_list():
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


async def create_categories(db_session: AsyncSession = None):
    """Create transaction categories."""

    subcategory_list = _get_subcategory_list()
    category_list = _get_category_list()

    if db_session:
        await _add_category_via_session(db_session, category_list, subcategory_list)
    else:
        _add_category_via_alembic_operator(category_list, subcategory_list)


def _add_category_via_alembic_operator(category_list, subcategory_list):
    category_table = table(
        "transactions_categories", column("id", sa.Integer), column("label", sa.String)
    )

    subcategory_table = table(
        "transactions_subcategories",
        column("label", sa.String),
        column("is_income", sa.Boolean),
        column("parent_category_id", sa.Integer),
    )

    op.bulk_insert(category_table, category_list)
    op.bulk_insert(subcategory_table, subcategory_list)


async def _add_category_via_session(db_session, category_list, subcategory_list):
    def create_subcategory_model(subcategory):
        return models.TransactionSubcategory(**subcategory)

    def create_category_model(category):
        return models.TransactionCategory(**category)

    subcategory = list(map(create_subcategory_model, subcategory_list))
    category = list(map(create_category_model, category_list))

    db_session.add_all(category + subcategory)
    await db_session.commit()
