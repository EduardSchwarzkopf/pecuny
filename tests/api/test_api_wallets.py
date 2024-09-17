import csv
import io
import time
from pathlib import Path
from typing import Any

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app import models, schemas
from app.data.categories import get_section_list
from app.date_manager import string_to_datetime
from app.repository import Repository
from app.utils.classes import RoundedDecimal, TransactionCSV
from app.utils.dataclasses_utils import ImportedTransaction
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_other_user_wallet, make_http_request

ENDPOINT = "/api/wallets/"


async def test_create_wallet(test_user: models.User, repository: Repository):
    """
    Test case for creating an wallet.

    Args:
        test_user (fixture): The test user.
        repository (fixture): The repository for database operations.
    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": "test_wallet", "description": "test", "balance": 500},
        as_user=test_user,
    )

    assert res.status_code == HTTP_201_CREATED

    new_wallet = schemas.WalletData(**res.json())

    wallet = await repository.get(models.Wallet, new_wallet.id)

    assert wallet is not None

    assert wallet.label == "test_wallet"
    assert wallet.balance == 500
    assert wallet.description == "test"


@pytest.mark.parametrize(
    "label",
    [
        (""),
        (None),
        (True),
    ],
)
async def test_invalid_title_create_wallet(test_user: models.User, label: Any):
    """
    Test case for creating an wallet with an invalid label.

    Args:
        test_user (fixture): The test user.
        label (Any): The label of the wallet.
    """

    res = await make_http_request(
        ENDPOINT,
        json={"label": label, "description": "test_invalid_title", "balance": 0},
        as_user=test_user,
    )

    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


async def test_delete_wallet(test_wallet: models.Wallet, repository: Repository):
    """
    Test case for deleting an wallet.

    Args:
        test_wallet (fixture): The test wallet.
        repository (fixture): The repository for database operations.
    """

    res = await make_http_request(
        f"{ENDPOINT}{test_wallet.id}",
        as_user=test_wallet.user,
        method=RequestMethod.DELETE,
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    wallet = await repository.get(models.Wallet, test_wallet.id)

    assert wallet is None


async def test_invalid_delete_wallet(
    test_user: models.User, test_wallet: models.Wallet, repository: Repository
):
    """
    Test case for deleting an wallet.

    Args:
        test_user (fixture): The test user.
        test_wallets (fixture): The list of test wallets.
        repository (fixture): The repository for database operations.
    """

    other_wallet = await get_other_user_wallet(test_user, repository)
    wallet_id = other_wallet.id

    res = await make_http_request(
        f"{ENDPOINT}{wallet_id}", as_user=test_user, method=RequestMethod.DELETE
    )

    assert res.status_code == HTTP_403_FORBIDDEN

    wallet_refresh = await repository.get(models.Wallet, wallet_id)

    assert isinstance(wallet_refresh, models.Wallet)
    assert wallet_refresh.id == wallet_id


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
async def test_update_wallet(
    test_wallet: models.Wallet,
    test_user: models.User,
    values: dict,
    repository: Repository,
):
    """
    Test case for updating an wallet.

    Args:
        test_wallet (fixture): The test wallet.
        test_user (fixture): The test user.
        values (dict): The updated values for the wallet.
        repository (fixture): The repository for database operations.
    """
    response = await make_http_request(
        f"{ENDPOINT}{test_wallet.id}", json=values, as_user=test_user
    )

    assert response.status_code == HTTP_200_OK
    wallet = schemas.WalletData(**response.json())

    db_wallet = await repository.get(models.Wallet, wallet.id)
    for key, value in values.items():
        wallet_val = getattr(wallet, key)
        db_wallet_val = getattr(db_wallet, key)
        print(f"key: {key} | value: {value} | wallet_val: {wallet_val}")
        if isinstance(value, float):

            assert db_wallet_val == RoundedDecimal(value)
            assert wallet_val == RoundedDecimal(value)

        else:
            assert db_wallet_val == value
            assert wallet_val == value


async def test_get_wallet_response(test_wallet):
    """
    Tests if the transaction amount in the JSON response is a float.

    Args:
        test_wallet (fixture): A wallet from the test_user.
    """

    res = await make_http_request(
        f"{ENDPOINT}{test_wallet.id}",
        as_user=test_wallet.user,
        method=RequestMethod.GET,
    )

    json_response = res.json()

    assert json_response["label"] == test_wallet.label
    assert json_response["description"] == test_wallet.description
    assert json_response["id"] == test_wallet.id
    assert isinstance(json_response["balance"], float)


async def test_import_transaction(
    test_wallet: models.Wallet,
    test_user: models.User,
    tmp_path: Path,
    repository: Repository,
):
    """
    Test case for importing transactions into an wallet.

    Args:
        test_wallet (fixture): The wallet to import transactions into.
        test_user (fixture): The user performing the import.
        tmp_path: Path to a temporary directory for file operations.
        repository (fixture): The repository for database operations.
    """

    wallet_id = test_wallet.id
    category = await repository.get(models.TransactionCategory, 1)
    assert category is not None

    section = await repository.get(models.TransactionSection, category.section_id)
    assert section is not None

    category_label = category.label
    section_label = section.label

    transactions = [
        ImportedTransaction(date, reference, amount, section_label, category_label)
        for date, reference, amount in [
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

    wallet_balance = test_wallet.balance

    with open(csv_file, "rb") as f:
        files = {"file": (csv_file.name, f, "text/csv")}
        response = await make_http_request(
            url=f"{ENDPOINT}{wallet_id}/import", files=files, as_user=test_user
        )

    assert response.status_code == HTTP_202_ACCEPTED

    time.sleep(1)

    # because the import is done in another session we also need a new one
    repository.session.expire_all()
    wallet_refresh = await repository.get(models.Wallet, wallet_id)
    assert wallet_refresh is not None
    new_balance = wallet_balance + total_amount
    assert new_balance == wallet_refresh.balance


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
    test_wallet: models.Wallet,
    tmp_path: Path,
    date: str,
    amount: float | str,
    category_id: int | str,
    repository: Repository,
):
    """
    Test case for importing transactions into an wallet.

    Args:
        test_wallet (fixture): The wallet to import transactions into.
        test_user (fixture): The user performing the import.
        tmp_path: Path to a temporary directory for file operations.
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

    wallet_id = test_wallet.id
    balance = test_wallet.balance

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
            url=f"{ENDPOINT}{test_wallet.id}/import",
            files={"file": (csv_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_202_ACCEPTED
    repository.session.expire_all()
    wallet_refresh = await repository.get(models.Wallet, wallet_id)
    assert wallet_refresh is not None
    assert balance == wallet_refresh.balance


async def test_invalid_import_transaction_file(
    test_user: models.User,
    test_wallet: models.Wallet,
    tmp_path: Path,
):
    """
    Test case for importing transactions into an wallet.

    Args:
        test_wallet (fixture): The wallet to import transactions into.
        test_user (fixture): The user performing the import.
        tmp_path: Path to a temporary directory for file operations.

    Returns:
        None
    """

    wallet_id = test_wallet.id
    empty_file: Path = tmp_path / "empty.csv"
    empty_file.write_text("")

    with open(empty_file, "rb") as f:
        response = await make_http_request(
            url=f"{ENDPOINT}{wallet_id}/import",
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
            url=f"{ENDPOINT}{wallet_id}/import",
            files={"file": (wrong_file.name, f, "text/csv")},
            as_user=test_user,
        )

    assert response.status_code == HTTP_400_BAD_REQUEST

    json_response = response.json()

    assert json_response.get("detail") == "Invalid file type"


async def test_example_import_file(
    test_wallet: models.Wallet,
    test_user: models.User,
    tmp_path: Path,
    repository: Repository,
):
    """
    Test case for importing transactions into an wallet.

    Args:
        test_wallet (fixture): The wallet to import transactions into.
        test_user (fixture): The user performing the import.
        tmp_path: Path to a temporary directory for file operations.

    Returns:
        None
    """

    filename = "pecuny_import_example.csv"
    response = await make_http_request(
        f"/static/data/{filename}", method=RequestMethod.GET
    )

    assert response.status_code == HTTP_200_OK

    file_path: Path = tmp_path / filename

    with open(file_path, "wb") as file:
        file.write(response.content)

    with open(file_path, "rb") as file:
        contents = file.read()
        assert contents is not None

        file_content_str = contents.decode("utf-8")
        file_like_object = io.StringIO(file_content_str)
        reader = csv.DictReader(file_like_object, delimiter=";")

        files = {"file": (file_path.name, file, "text/csv")}
        response = await make_http_request(
            url=f"{ENDPOINT}{test_wallet.id}/import", files=files, as_user=test_user
        )

        assert response.status_code == HTTP_202_ACCEPTED

        time.sleep(1)  # give the queue some time to process
        repository.session.expire_all()

        for row in reader:
            date = row.get("date")
            assert date is not None

            transaction_date = string_to_datetime(date)
            transaction_category = row.get("category")
            transaction_section = row.get("section")

            transaction_information_list = await repository.filter_by_multiple(
                models.TransactionInformation,
                [
                    (
                        models.TransactionInformation.amount,
                        row.get("amount"),
                        DatabaseFilterOperator.EQUAL,
                    ),
                    (
                        models.TransactionInformation.date,
                        transaction_date,
                        DatabaseFilterOperator.EQUAL,
                    ),
                    (
                        models.TransactionInformation.reference,
                        row.get("reference"),
                        DatabaseFilterOperator.EQUAL,
                    ),
                ],
            )

            assert len(transaction_information_list) == 1

            transaction = transaction_information_list[0]

            assert transaction is not None
            assert transaction.category.label == transaction_category
            assert transaction.category.section.label == transaction_section
