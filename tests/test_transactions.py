import datetime

import pytest
from fastapi import status

from app import models
from app import repository as repo
from app import schemas
from app.utils.dataclasses_utils import ClientSessionWrapper
from tests.helpers import make_http_request

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
@pytest.mark.usefixtures("test_account")
async def test_create_transaction(
    client_session_wrapper: ClientSessionWrapper,
    amount,
    expected_amount,
    reference,
    category_id,
    test_account,
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
        client_session_wrapper.session,
        client_session_wrapper.authorized_client,
        ENDPOINT,
        json={
            "account_id": test_account.id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.now(datetime.timezone.utc)),
            "category_id": category_id,
        },
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
@pytest.mark.usefixtures("test_transactions")
async def test_updated_transaction(
    client_session_wrapper: ClientSessionWrapper,
    category_id,
    amount,
    test_account,
):
    """
    Tests the updated transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        transaction_id: The ID of the transaction.
        category_id: The ID of the category.
        amount: The amount of the transaction.

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
        client_session_wrapper.session,
        client_session_wrapper.authorized_client,
        f"{ENDPOINT}{transaction.id}",
        json=json,
    )

    assert res.status_code == status.HTTP_200_OK
    transaction = schemas.Transaction(**res.json())

    updated_test_account = await repo.get(models.Account, test_account.id)

    difference = transaction_amount_before - amount

    assert updated_test_account.balance == round(account_balance - difference, 2)
    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


@pytest.mark.parametrize(
    "transaction_id",
    [
        (1),
        (2),
    ],
)
@pytest.mark.usefixtures("test_transactions")
async def test_delete_transaction(
    client_session_wrapper: ClientSessionWrapper,
    transaction_id,
):
    """
    Tests the delete transaction functionality.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        transaction_id: The ID of the transaction.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        account = await repo.get(models.Account, ACCOUNT_ID)
        await repo.refresh(account)  # session not updated, so we need to refresh first
        account_balance = account.balance
        transaction = await repo.get(models.Transaction, transaction_id)
        amount = transaction.information.amount

        res = await client_session_wrapper.authorized_client.delete(
            f"{ENDPOINT}{transaction_id}"
        )
        assert res.status_code == status.HTTP_204_NO_CONTENT

        await repo.refresh(account)
    account_balance_after = account.balance

    assert account_balance_after == (account_balance - amount)


@pytest.mark.parametrize(
    "transaction_id",
    [
        (3),
        (9999),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_delete_transaction_fail(
    client_session_wrapper: ClientSessionWrapper,
    transaction_id,
):
    """
    Tests the delete transaction functionality, which should fail.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        transaction_id: The ID of the transaction.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        account = await repo.get(models.Account, ACCOUNT_ID)
        await repo.refresh(account)  # session not updated, so we need to refresh first
        account_balance = account.balance

        res = await client_session_wrapper.authorized_client.delete(
            f"{ENDPOINT}{transaction_id}"
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        await repo.refresh(account)
    account_balance_after = account.balance

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
@pytest.mark.usefixtures("test_accounts")
async def test_create_offset_transaction(
    client_session_wrapper: ClientSessionWrapper,
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

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={
                "account_id": ACCOUNT_ID,
                "amount": amount,
                "reference": reference,
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": OFFSET_ACCOUNT_ID,
            },
        )

        assert res.status_code == status.HTTP_201_CREATED

        new_transaction = schemas.Transaction(**res.json())
        offset_transactions_id = new_transaction.offset_transactions_id

        new_offset_transaction = await repo.get(
            models.Transaction, offset_transactions_id
        )
        await repo.refresh(new_offset_transaction)

    assert new_transaction.account_id == ACCOUNT_ID
    assert new_offset_transaction.account_id == OFFSET_ACCOUNT_ID

    assert new_transaction.information.amount == round(amount, 2)
    assert new_offset_transaction.information.amount == round(expected_offset_amount, 2)

    assert isinstance(new_transaction.information.amount, float)
    assert isinstance(new_offset_transaction.information.amount, float)

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


@pytest.mark.parametrize(
    "offset_account_id, amount",
    [
        (2, 10),
        (3, 20.5),
        (4, -30.5),
        (2, -40.5),
        (2, 5.9999999999),
        (2, 1.00000000004),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_create_offset_transaction_other_account_fail(
    client_session_wrapper: ClientSessionWrapper,
    offset_account_id,
    amount,
):
    """
    Tests the create offset transaction functionality with a different account,
    which should fail.

    Args:
        client_session_wrapper: The client session wrapper fixture.
        offset_account_id: The ID of the offset account.
        amount: The amount of the transaction.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        account = await repo.get(models.Account, ACCOUNT_ID)
        offset_account = await repo.get(models.Account, offset_account_id)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={
                "account_id": ACCOUNT_ID,
                "amount": amount,
                "reference": "Not allowed",
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": 1,
                "offset_account_id": offset_account_id,
            },
        )

        await repo.refresh_all([account, offset_account])

    account_balance_after = account.balance
    offset_account_balance_after = offset_account.balance

    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    assert account_balance == account_balance_after
    assert offset_account_balance == offset_account_balance_after


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
    client_session_wrapper: ClientSessionWrapper,
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

    async with client_session_wrapper.session:
        account = await repo.get(models.Account, ACCOUNT_ID)
        offset_account = await repo.get(models.Account, OFFSET_ACCOUNT_ID)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        transaction_res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={
                "account_id": ACCOUNT_ID,
                "amount": amount + 5,
                "reference": "creation",
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": OFFSET_ACCOUNT_ID,
            },
        )

        transaction_before = schemas.Transaction(**transaction_res.json())

        reference = f"Offset_transaction with {amount}"
        res = await client_session_wrapper.authorized_client.post(
            f"{ENDPOINT}{transaction_before.id}",
            json={
                "account_id": ACCOUNT_ID,
                "amount": amount,
                "reference": reference,
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
            },
        )

        assert res.status_code == status.HTTP_200_OK

        await repo.refresh_all([account, offset_account])

    transaction = schemas.Transaction(**res.json())

    assert account.balance == round(account_balance + amount, 2)
    assert offset_account.balance == round(offset_account_balance - amount, 2)

    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


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
async def test_delete_offset_transaction(
    client_session_wrapper: ClientSessionWrapper,
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

    async with client_session_wrapper.session:
        account = await repo.get(models.Account, ACCOUNT_ID)
        offset_account = await repo.get(models.Account, OFFSET_ACCOUNT_ID)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        transaction_res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={
                "account_id": ACCOUNT_ID,
                "amount": amount,
                "reference": "creation",
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": ACCOUNT_ID,
            },
        )

        transaction = schemas.Transaction(**transaction_res.json())

        res = await client_session_wrapper.authorized_client.delete(
            f"{ENDPOINT}{transaction.id}"
        )
        offset_transaction_res = await client_session_wrapper.authorized_client.get(
            f"{ENDPOINT}{transaction.offset_transactions_id}"
        )

        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert offset_transaction_res.status_code == status.HTTP_404_NOT_FOUND

        await repo.refresh_all([account, offset_account])

    assert offset_account_balance == offset_account.balance
    assert account_balance == account.balance
