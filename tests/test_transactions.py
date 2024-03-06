import datetime
from typing import List

import pytest
from fastapi import status

from app import models
from app import repository as repo
from app import schemas
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import get_user_offset_account, make_http_request

ENDPOINT = "/api/transactions/"
STATUS_CODE = status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "amount, expected_amount, reference, category_id",
    [
        (10, 10, "Added 10", 1),
        (20.5, 20.5, "Added 20.5", 3),
        (-30.5, -30.5, "Substract 30.5", 6),
        (-40.5, -40.5, "Subsctract 40.5", 6),
    ],
)
async def test_create_transaction(
    amount, expected_amount, reference, category_id, test_account, test_user
):
    """
    Tests the create transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        amount: The amount of the transaction.
        expected_amount: The expected amount of the transaction.
        reference: The reference of the transaction.
        category_id: The ID of the category.

    Returns:
        None
    """

    account_balance = test_account.balance

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": test_account.id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
        },
        as_user=test_user,
    )

    new_transaction = schemas.Transaction(**res.json())

    assert res.status_code == status.HTTP_201_CREATED
    assert account_balance + amount == test_account.balance
    assert new_transaction.account_id == test_account.id
    assert new_transaction.information.amount == expected_amount
    assert isinstance(new_transaction.information.amount, float)
    assert new_transaction.information.reference == reference


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 2.5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -25),
        (1, -35),
        (1, -0.3333333334),
        (7, 0),
    ],
)
@pytest.mark.usefixtures("fixture_create_transactions")
async def test_updated_transaction(category_id, amount, test_account, test_user):
    """
    Test case for updating a transaction.

    Args:
        client_session_wrapper: The client session wrapper.
        category_id: The category ID.
        amount: The amount.
        test_account: The test account.

    Returns:
        None
    """

    reference = f"Updated Val {amount}"

    json = {
        "account_id": test_account.id,
        "amount": amount,
        "reference": f"Updated Val {amount}",
        "date": str(datetime.datetime.now(datetime.timezone.utc)),
        "category_id": category_id,
    }

    account_balance = test_account.balance

    transaction_list = await repo.filter_by(
        models.Transaction, "account_id", test_account.id
    )

    transaction = transaction_list[0]
    transaction_amount_before = transaction.information.amount

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}", json=json, as_user=test_user
    )

    assert res.status_code == status.HTTP_200_OK
    transaction = schemas.Transaction(**res.json())

    updated_test_account = await repo.get(models.Account, test_account.id)

    difference = transaction_amount_before - amount

    assert updated_test_account.balance == round(account_balance - difference, 2)
    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


async def test_delete_transactions(
    test_account: models.Account,
    test_account_transaction_list: List[models.Transaction],
    test_user: models.User,
):
    """
    Test case for deleting a transaction.

    Args:
        client_session_wrapper: The client session wrapper.
        test_account: The test account.
        test_account_transaction_list: The list of test account transactions.

    Returns:
        None
    """
    for transaction in test_account_transaction_list:

        account_balance = test_account.balance
        amount = transaction.information.amount
        transaction_id = transaction.id

        res = await make_http_request(
            f"{ENDPOINT}{transaction_id}",
            method=RequestMethod.DELETE,
            as_user=test_user,
        )
        assert res.status_code == status.HTTP_204_NO_CONTENT
        result = await repo.get(models.Transaction, transaction_id)

        assert result is None

        account = await repo.get(models.Account, test_account.id)
        account_balance_after = account.balance

        expected_balance = account_balance - amount
        assert account_balance_after == expected_balance

        assert await repo.get(models.Transaction, transaction_id) is None


@pytest.mark.usefixtures("fixture_create_transactions")
async def test_delete_transactions_fail(test_account: models.Account, test_user):
    """
    Test case for failing to delete transactions.

    Args:
        client_session_wrapper: The client session wrapper.
        test_account: The test account.
        test_transactions: The list of test transactions.

    Returns:
        None
    """

    result = await repo.filter_by(
        models.Account,
        "user_id",
        test_account.user_id,
        DatabaseFilterOperator.NOT_EQUAL,
        load_relationships_list=[models.Account.transactions],
    )
    account = result[0]

    account_balance = account.balance

    for transaction in account.transactions:

        res = await make_http_request(
            f"{ENDPOINT}{transaction.id}",
            method=RequestMethod.DELETE,
            as_user=test_user,
        )

        assert res.status_code == status.HTTP_404_NOT_FOUND

        account_refresh = await repo.get(models.Account, account.id)
        account_balance_after = account_refresh.balance

        assert account_balance_after == account_balance


@pytest.mark.parametrize(
    "amount, expected_offset_amount, reference, category_id",
    [
        (10, -10, "Added 10", 1),
        (20.5, -20.5, "Added 20.5", 3),
        (-30.5, 30.5, "Substract 30.5", 6),
        (-40.5, 40.5, "Substract 40.5", 6),
        (5.9999999999, -6, "Added 6", 6),
        (1.00000000004, -1, "Added 1", 6),
    ],
)
async def test_create_offset_transaction(
    test_account: models.Account,
    test_accounts: List[models.Account],
    test_user: models.User,
    amount,
    expected_offset_amount,
    reference,
    category_id,
):
    """
    Tests the create offset transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        amount: The amount of the transaction.
        expected_offset_amount: The expected amount of the offset transaction.
        reference: The reference of the transaction.
        category_id: The ID of the category.

    Returns:
        None
    """

    account_id = test_account.id
    offset_account = get_user_offset_account(test_account, test_accounts)

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account.id,
        },
        as_user=test_user,
    )

    assert res.status_code == status.HTTP_201_CREATED

    new_transaction = schemas.Transaction(**res.json())
    offset_transactions_id = new_transaction.offset_transactions_id

    new_offset_transaction = await repo.get(models.Transaction, offset_transactions_id)

    assert new_transaction.account_id == account_id
    assert new_offset_transaction.account_id == offset_account.id

    assert new_transaction.information.amount == round(amount, 2)
    assert new_offset_transaction.information.amount == round(expected_offset_amount, 2)

    assert isinstance(new_transaction.information.amount, float)
    assert isinstance(new_offset_transaction.information.amount, float)

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


async def test_create_offset_transaction_other_account_fail(
    test_account: models.Account,
    test_accounts: List[models.Account],
    test_user: models.User,
):

    for offset_account in test_accounts:
        if offset_account.user_id != test_account.user_id:
            break

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance
    account_id = test_account.id
    offset_account_id = offset_account.id

    res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": 42,
            "reference": "Not allowed",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": 1,
            "offset_account_id": offset_account_id,
        },
        as_user=test_user,
    )

    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    account_refreshed = await repo.get(models.Account, account_id)
    offset_account_refreshed = await repo.get(models.Account, offset_account_id)

    assert account_balance == account_refreshed.balance
    assert offset_account_balance == offset_account_refreshed.balance


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 2.5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -25),
        (1, -35),
        (1, -0.3333333334),
        (7, 0),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_updated_offset_transaction(
    test_account: models.Account,
    test_accounts: List[models.Account],
    test_user: models.User,
    category_id,
    amount,
):
    """
    Tests the updated offset transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        category_id: The ID of the category.
        amount: The amount of the transaction.

    Returns:
        None
    """

    offset_account = get_user_offset_account(test_account, test_accounts)

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance
    account_id = test_account.id
    offset_account_id = offset_account.id

    # create base transaction
    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": account_id,
            "amount": 5,
            "reference": "creation",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account_id,
        },
        as_user=test_user,
    )

    transaction_before = schemas.Transaction(**transaction_res.json())

    reference = f"Offset_transaction with {amount}"
    res = await make_http_request(
        f"{ENDPOINT}{transaction_before.id}",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
        },
        as_user=test_user,
    )

    assert res.status_code == status.HTTP_200_OK

    transaction = schemas.Transaction(**res.json())

    account_refreshed = await repo.get(models.Account, account_id)
    offset_account_refreshed = await repo.get(models.Account, offset_account_id)

    assert account_refreshed.balance == round(account_balance + amount, 2)
    assert offset_account_refreshed.balance == round(offset_account_balance - amount, 2)

    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


@pytest.mark.parametrize(
    "category_id, amount",
    [
        (1, 5),
        (1, 0),
        (2, 3.666666666667),
        (3, 0.133333333334),
        (4, -2.5),
        (1, -35),
        (1, -0.3333333334),
        (7, 05.5),
    ],
)
@pytest.mark.usefixtures()
async def test_delete_offset_transaction(
    test_account: models.Account,
    test_accounts: List[models.Account],
    test_user: models.User,
    category_id,
    amount,
):
    """
    Tests the delete offset transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        category_id: The ID of the category.
        amount: The amount of the transaction.

    Returns:
        None
    """

    offset_account = get_user_offset_account(test_account, test_accounts)

    account_balance = test_account.balance
    offset_account_balance = offset_account.balance

    transaction_res = await make_http_request(
        ENDPOINT,
        json={
            "account_id": test_account.id,
            "amount": amount,
            "reference": "creation",
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
            "offset_account_id": offset_account.id,
        },
        as_user=test_user,
    )

    transaction = schemas.Transaction(**transaction_res.json())

    res = await make_http_request(
        f"{ENDPOINT}{transaction.id}", as_user=test_user, method=RequestMethod.DELETE
    )
    offset_transaction_res = await make_http_request(
        f"{ENDPOINT}{transaction.offset_transactions_id}",
        as_user=test_user,
        method=RequestMethod.GET,
    )

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert offset_transaction_res.status_code == status.HTTP_404_NOT_FOUND

    account_refresh = await repo.get(models.Account, test_account.id)
    offset_account_refresh = await repo.get(models.Account, offset_account.id)

    assert offset_account_balance == offset_account_refresh.balance
    assert account_balance == account_refresh.balance
