from datetime import datetime as dt
from datetime import timedelta
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
    section = await repository.get(models.TransactionSection, category.section_id)
    category_label = category.label
    section_label = section.label

    transactions = [
        ImportedTransaction(
            "08.03.2024", "VISA OPENAI", -0.23, section_label, category_label
        ),
        ImportedTransaction(
            "08.03.2024", "VISA OPENAI", -11.69, section_label, category_label
        ),
        ImportedTransaction(
            "07.03.2024", "Restaurant", -11.95, section_label, category_label
        ),
        ImportedTransaction(
            "07.03.2024", "ROSSMANN", -44.51, section_label, category_label
        ),
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
    "transaction_data",
    [
        (["banane", "", "Test", -0.23, 1]),
        (["08.03.2024", "", "Test", -0.23, "kaputt"]),
        (["08.03.2024", "", "Test", "FAIL", 1]),
    ],
)
async def test_invalid_import_transaction_file(
    test_user: models.User,
    test_account: models.Account,
    tmp_path: Path,
    transaction_data: List,
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

    csv_data = [tuple(transaction_data)]
    csv_obj = TransactionCSV(csv_data)

    csv_content = csv_obj.generate_csv_content()
    csv_file: Path = tmp_path / "transactions.csv"
    csv_file.write_text(csv_content)

    with open(csv_file, "rb") as f:
        files = {"file": (csv_file.name, f, "text/csv")}
        response = await make_http_request(
            url=f"{ENDPOINT}{test_account.id}/import", files=files, as_user=test_user
        )

    assert response.status_code == HTTP_400_BAD_REQUEST


async def test_import_transaction_fail(
    test_user: models.User,
    test_account: models.Account,
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
    user_id = test_user.id
    non_existing_id = 999999
    date = "08.03.2024"

    csv_obj = TransactionCSV(
        [
            (date, "", "Test", 100, non_existing_id),
        ]
    )

    csv_file: Path = tmp_path / "transactions.csv"
    csv_file.write_text(csv_obj.generate_csv_content())

    with open(csv_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{account_id}/import",
            files={"file": (csv_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_202_ACCEPTED

    csv_obj = TransactionCSV(
        [
            (date, "", "Test", 100, 1),
        ]
    )

    user = await repository.get(models.User, user_id)
    with open(csv_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{non_existing_id}/import",
            files={"file": (csv_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_202_ACCEPTED

    input_date = dt.strptime(date, "%d.%m.%Y")

    start_of_day = input_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

    repository.session.expire_all()
    user = await repository.get(models.User, user_id)
    response = await make_http_request(
        url="/api/transactions/",
        as_user=user,
        method=RequestMethod.GET,
        params={
            "account_id": account_id,
            "date_start": start_of_day.isoformat(),
            "date_end": end_of_day.isoformat(),
        },
    )

    assert response.status_code == HTTP_200_OK

    assert len(response.json()) == 0
