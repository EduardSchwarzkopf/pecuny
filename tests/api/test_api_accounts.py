from pathlib import Path
from typing import Any, List

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app import models, schemas
from app.data.categories import get_section_list
from app.repository import Repository
from app.utils.classes import RoundedDecimal, TransactionCSV
from app.utils.dataclasses_utils import ImportedTransaction
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

ENDPOINT = "/api/accounts/"


async def test_create_account(test_user: models.User):
    """
    Test case for creating an account.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": "test_account", "description": "test", "balance": 500},
        as_user=test_user,
    )

    assert res.status_code == HTTP_201_CREATED

    new_account = schemas.Account(**res.json())

    assert new_account.label == "test_account"
    assert new_account.balance == 500
    assert new_account.description == "test"


@pytest.mark.parametrize(
    "label",
    [
        (""),
        (None),
        (True),
    ],
)
async def test_invalid_title_create_account(test_user: models.User, label: Any):
    """
    Test case for creating an account with an invalid label.

    Args:
        test_user (fixture): The test user.
        label (Any): The label of the account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": label, "description": "test_invalid_title", "balance": 0},
        as_user=test_user,
    )

    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


async def test_delete_account(test_account: models.Account, repository: Repository):
    """
    Test case for deleting an account.

    Args:
        test_account (fixture): The test account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    res = await make_http_request(
        f"{ENDPOINT}{test_account.id}",
        as_user=test_account.user,
        method=RequestMethod.DELETE,
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    account = await repository.get(models.Account, test_account.id)

    assert account is None


async def test_invalid_delete_account(
    test_user: models.User, test_accounts: List[models.Account], repository: Repository
):
    """
    Test case for deleting an account.

    Args:
        test_user (fixture): The test user.
        test_accounts (fixture): The list of test accounts.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    for account in test_accounts:

        if account.user_id == test_user.id:
            continue

        res = await make_http_request(
            f"{ENDPOINT}{account.id}", as_user=test_user, method=RequestMethod.DELETE
        )

        assert res.status_code == HTTP_404_NOT_FOUND

        account_refresh = await repository.get(models.Account, account.id)

        assert account_refresh == account


@pytest.mark.parametrize(
    "values",
    [
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": 1111.3,
        },
        {
            "label": "11113",
            "description": "cool story bro '",
            "balance": 2000,
        },
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": -0.333333334,
        },
        {
            "label": "My new Label",
            "description": "very new description",
            "balance": -1000000.3,
        },
    ],
)
async def test_update_account(
    test_account: models.Account,
    test_user: models.User,
    values: dict,
    repository: Repository,
):
    """
    Test case for updating an account.

    Args:
        test_account (fixture): The test account.
        test_user (fixture): The test user.
        values (dict): The updated values for the account.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """
    response = await make_http_request(
        f"{ENDPOINT}{test_account.id}", json=values, as_user=test_user
    )

    assert response.status_code == HTTP_200_OK
    account = schemas.AccountData(**response.json())

    db_account = await repository.get(models.Account, account.id)
    for key, value in values.items():
        account_val = getattr(account, key)
        db_account_val = getattr(db_account, key)
        print(f"key: {key} | value: {value} | account_val: {account_val}")
        if isinstance(value, float):

            assert db_account_val == RoundedDecimal(value)
            assert account_val == RoundedDecimal(value)

        else:
            assert db_account_val == value
            assert account_val == value


async def test_get_account_response(test_account):
    """
    Tests if the transaction amount in the JSON response is a float.

    Args:
        test_account_transaction_list (fixture): The list of account transactions.
        test_user (fixture): The test user.
    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    res = await make_http_request(
        f"{ENDPOINT}{test_account.id}",
        as_user=test_account.user,
        method=RequestMethod.GET,
    )

    json_response = res.json()

    assert json_response["label"] == test_account.label
    assert json_response["description"] == test_account.description
    assert json_response["id"] == test_account.id
    assert isinstance(json_response["balance"], float)


async def test_import_transaction(
    test_account: models.Account,
    test_user: models.User,
    tmp_path: Path,
    repository: Repository,
):
    """
    Test case for importing transactions into an account.

    Args:
        test_account: The account to import transactions into.
        test_user: The user performing the import.
        tmp_path: Path to a temporary directory for file operations.

    Returns:
        None
    """

    account_id = test_account.id
    category = await repository.get(models.TransactionCategory, 1)
    assert category is not None

    section = await repository.get(models.TransactionSection, category.section_id)
    assert section is not None

    category_label = category.label
    section_label = section.label

    transactions = [
        ImportedTransaction(date, description, amount, section_label, category_label)
        for date, description, amount in [
            ("08.03.2024", "VISA OPENAI", -0.23),
            ("08.03.2024", "VISA OPENAI", -11.69),
            ("07.03.2024", "Restaurant", -11.95),
            ("07.03.2024", "ROSSMANN", -44.51),
        ]
    ]

    csv_obj = TransactionCSV(transactions)
    total_amount = csv_obj.calculate_total_amount()

    csv_content = csv_obj.generate_csv_content()
    csv_file: Path = tmp_path / "transactions.csv"
    csv_file.write_text(csv_content)

    account_balance = test_account.balance

    with open(csv_file, "rb") as f:
        files = {"file": (csv_file.name, f, "text/csv")}
        response = await make_http_request(
            url=f"{ENDPOINT}{account_id}/import", files=files, as_user=test_user
        )

    assert response.status_code == HTTP_202_ACCEPTED

    # because the import is done in another session we also need a new one
    repository.session.expire_all()
    account_refresh = await repository.get(models.Account, account_id)
    assert account_refresh is not None
    new_balance = account_balance + total_amount
    assert new_balance == account_refresh.balance


@pytest.mark.parametrize(
    "date, amount, category_id",
    [
        ("banane", -0.23, 1),
        ("08.03.2024", -0.23, "kaputt"),
        ("08.03.2024", "FAIL", 1),
    ],
)
async def test_import_transaction_fail(
    test_user: models.User,
    test_account: models.Account,
    tmp_path: Path,
    date: str,
    amount: float | str,
    category_id: int | str,
    repository: Repository,
):
    """
    Test case for importing transactions into an account.

    Args:
        test_account: The account to import transactions into.
        test_user: The user performing the import.
        tmp_path: Path to a temporary directory for file operations.

    Returns:
        None
    """

    category_label = category_id
    section_list = get_section_list()
    section_label = section_list[0].get("label")
    if isinstance(category_id, int):
        category = await repository.get(models.TransactionCategory, category_id)
        assert category is not None
        section = await repository.get(models.TransactionSection, category.section_id)
        assert section is not None

        category_label = category.label
        section_label = section.label

    account_id = test_account.id
    balance = test_account.balance

    transaction_data = [
        ImportedTransaction(
            date=date,
            reference="Test Invalid file",
            amount=amount,
            section=section_label,
            category=category_label,
        )
    ]
    csv_obj = TransactionCSV(transaction_data)

    csv_file: Path = tmp_path / "transactions.csv"
    csv_file.write_text(csv_obj.generate_csv_content())

    with open(csv_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{test_account.id}/import",
            files={"file": (csv_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_202_ACCEPTED
    repository.session.expire_all()
    account_refresh = await repository.get(models.Account, account_id)
    assert account_refresh is not None
    assert balance == account_refresh.balance


async def test_invalid_import_transaction_file(
    test_user: models.User,
    test_account: models.Account,
    tmp_path: Path,
):
    """
    Test case for importing transactions into an account.

    Args:
        test_account: The account to import transactions into.
        test_user: The user performing the import.
        tmp_path: Path to a temporary directory for file operations.

    Returns:
        None
    """

    account_id = test_account.id
    empty_file: Path = tmp_path / "empty.csv"
    empty_file.write_text("")

    with open(empty_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{account_id}/import",
            files={"file": (empty_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_400_BAD_REQUEST

    json_response = response.json()
    assert json_response.get("detail") == "File is empty"

    wrong_file: Path = tmp_path / "import.fail"
    wrong_file.write_text("some content")

    with open(wrong_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{account_id}/import",
            files={"file": (wrong_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_400_BAD_REQUEST

    json_response = response.json()

    assert json_response.get("detail") == "Invalid file type"
