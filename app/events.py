from sqlalchemy.orm.session import Session


def create_categories(db_session: Session):
    """Create transaction categories."""
    from .models import TransactionSubcategory, TransactionCategory

    income_cats = [("Salary", True), ("Support", True), ("Other income", True)]

    housing_cats = [
        ("Rent", False),
        ("Heating", False),
        ("Electricity", False),
        ("Water", False),
        ("Renovation/Repair", False),
        ("TV licence", False),  # de: GEZ
        ("Phone and internet", False),
        ("Furniture", False),
        ("Electric appliances", False),
    ]

    houshold_cats = [
        ("Detergent", False),
        ("Groceries", False),
        ("Beverages", False),
        ("Drink and tobacco", False),  # de Genussmittell
        ("Medication", False),
        ("Hygiene products", False),
    ]

    leisure_cats = [
        ("Restaurant", False),
        ("Hobby", False),
        ("Gym", False),
        ("Pets", False),
        ("Membership contribution", False),  # de: Vereinsbeiträge
        ("Gaming", False),
        ("Vacation", False),
        ("Trips", False),
        ("Hairdresser", False),
        ("Cosmetic", False),
        ("Clothing", False),
        ("Magazines and books", False),
    ]

    work_cats = [
        ("Furniture", False),
        ("Work materials", False),  # de: Arbeitsutensilien
        ("Mailings", False),
        ("Workwear", False),
        ("Travel expenses", False),
    ]

    transport_cats = [
        ("Public transport", False),
        ("Gas", False),  # de: Tanken
        ("Car repairs", False),
        ("Car care", False),
        ("Vehicle tax", False),  # de: KFZ-Steuer
    ]

    education_cats = [
        ("Semester fees", False),
        ("school fees", False),
        ("Travel expenses", False),
        ("Teaching aids", False),
        ("Course fees", False),
    ]

    insurance_cats = [
        ("Pension insurance", False),
        ("Health insurance", False),
        ("Liability insurance", False),
        ("Car insurance", False),
        ("Occupational disability insurance", False),
        ("Accident insurance", False),
        ("Term life insurance", False),  # de: Risikolebensversicherung
        ("Home insurance", False),
        ("Life insurance", False),
    ]

    finance_cats = [
        ("Loans", False),
        ("Pocket Money", False),
        ("Alimony", False),
        ("Reserves", False),
    ]

    other_cats = [
        ("Medical Expenses", False),
        ("Bank Fees", False),
        ("Tax consultancy", False),
        ("Tax", False),
    ]

    data = {
        "Income": income_cats,
        "Work": work_cats,
        "Housing": housing_cats,
        "Houshold": houshold_cats,
        "Insurance": insurance_cats,
        "Transport": transport_cats,
        "Financing": finance_cats,
        "Education": education_cats,
        "Leisure": leisure_cats,
        "Others": other_cats,
    }

    for categorie, subcategories in data.items():

        result = (
            db_session.query(TransactionCategory).filter_by(label=categorie).first()
        )
        commit = False

        if not result:
            transaction_category = TransactionCategory(label=categorie)
            commit = True
            db_session.add(transaction_category)
        else:
            transaction_category = result

        for subcategory_data in subcategories:

            subcategory_label = subcategory_data[0]
            result_sub = (
                db_session.query(TransactionSubcategory)
                .filter_by(label=subcategory_label)
                .first()
            )

            if result_sub:
                continue

            commit = True
            parent_category = transaction_category.id
            new_sub = TransactionSubcategory(
                label=subcategory_label,
                parent_category_id=parent_category,
                is_income=subcategory_data[1],
            )
            db_session.add(new_sub)

        if commit:
            db_session.commit()


if __name__ == "__main__":
    create_categories()
