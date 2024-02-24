import datetime

import pytest

from app import models
from app import repository as repo
from app import schemas
from tests.fixtures import ClientSessionWrapper

#
# use with: pytest --disable-warnings -v -x
#

pytestmark = pytest.mark.anyio
endpoint = "/api/transactions/"


@pytest.mark.parametrize(
    "account_id, amount, expected_amount, reference, category_id, status_code",
    [
        (1, 10, 10, "Added 10", 1, 201),
        (1, 20.5, 20.5, "Added 20.5", 3, 201),
        (1, -30.5, -30.5, "Substract 30.5", 6, 201),
        (1, -40.5, -40.5, "Subsctract 40.5", 6, 201),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_create_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    amount,
    expected_amount,
    reference,
    category_id,
    status_code,
):
    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)

        account_balance = account.balance

        res = await client_session_wrapper_fixture.authorized_client.post(
            endpoint,
            json={
                "account_id": account_id,
                "amount": amount,
                "reference": reference,
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
            },
        )

        new_transaction = schemas.Transaction(**res.json())

        await repo.refresh(account)

        account_balance_after = account.balance

    assert res.status_code == status_code
    assert account_balance + amount == account_balance_after
    assert new_transaction.account_id == account_id
    assert new_transaction.information.amount == expected_amount
    assert type(new_transaction.information.amount) == float
    assert new_transaction.information.reference == reference


@pytest.mark.parametrize(
    "account_id, transaction_id, category_id, amount, status_code",
    [
        (1, 1, 1, 2.5, 200),
        (1, 2, 1, 0, 200),
        (1, 1, 2, 3.666666666667, 200),
        (1, 2, 3, 0.133333333334, 200),
        (1, 2, 4, -25, 200),
        (1, 1, 1, -35, 200),
        (1, 1, 1, -0.3333333334, 200),
        (1, 1, 7, 0, 200),
    ],
)
@pytest.mark.usefixtures("test_transactions")
async def test_updated_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    transaction_id,
    category_id,
    amount,
    status_code,
):
    reference = f"Updated Val {amount}"

    json = {
        "account_id": account_id,
        "amount": amount,
        "reference": f"Updated Val {amount}",
        "date": str(datetime.datetime.now(datetime.timezone.utc)),
        "category_id": category_id,
    }

    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        account_balance = account.balance

        transaction_before = await repo.get(models.Transaction, transaction_id)
        transaction_amount_before = transaction_before.information.amount

        res = await client_session_wrapper_fixture.authorized_client.post(
            f"{endpoint}{transaction_id}", json=json
        )

        assert res.status_code == status_code
        t = res.json()

        await repo.refresh(account)

    account_balance_after = account.balance

    transaction = schemas.Transaction(**res.json())

    difference = transaction_amount_before - amount

    assert account_balance_after == round(account_balance - difference, 2)
    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


@pytest.mark.parametrize(
    "account_id, transaction_id, status_code",
    [
        (1, 1, 204),
        (1, 2, 204),
    ],
)
@pytest.mark.usefixtures("test_transactions")
async def test_delete_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    transaction_id,
    status_code,
):
    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        await repo.refresh(account)  # session not updated, so we need to refresh first
        account_balance = account.balance
        transaction = await repo.get(models.Transaction, transaction_id)
        amount = transaction.information.amount

        res = await client_session_wrapper_fixture.authorized_client.delete(
            f"{endpoint}{transaction_id}"
        )
        assert res.status_code == status_code

        await repo.refresh(account)
    account_balance_after = account.balance

    assert account_balance_after == (account_balance - amount)


@pytest.mark.parametrize(
    "account_id, transaction_id, status_code",
    [
        (1, 3, 404),
        (1, 9999, 404),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_delete_transaction_fail(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    transaction_id,
    status_code,
):
    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        await repo.refresh(account)  # session not updated, so we need to refresh first
        account_balance = account.balance

        res = await client_session_wrapper_fixture.authorized_client.delete(
            f"{endpoint}{transaction_id}"
        )
        assert res.status_code == status_code

        await repo.refresh(account)
    account_balance_after = account.balance

    assert account_balance_after == account_balance


@pytest.mark.parametrize(
    "account_id, offset_account_id, amount, expected_offset_amount, reference, category_id, status_code",
    [
        (1, 5, 10, -10, "Added 10", 1, 201),
        (1, 5, 20.5, -20.5, "Added 20.5", 3, 201),
        (1, 5, -30.5, 30.5, "Substract 30.5", 6, 201),
        (1, 5, -40.5, 40.5, "Substract 40.5", 6, 201),
        (1, 5, 5.9999999999, -6, "Added 6", 6, 201),
        (1, 5, 1.00000000004, -1, "Added 1", 6, 201),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_create_offset_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    offset_account_id,
    amount,
    expected_offset_amount,
    reference,
    category_id,
    status_code,
):
    async with client_session_wrapper_fixture.session:
        res = await client_session_wrapper_fixture.authorized_client.post(
            endpoint,
            json={
                "account_id": account_id,
                "amount": amount,
                "reference": reference,
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": offset_account_id,
            },
        )

        assert res.status_code == status_code

        new_transaction = schemas.Transaction(**res.json())
        offset_transactions_id = new_transaction.offset_transactions_id

        new_offset_transaction = await repo.get(
            models.Transaction, offset_transactions_id
        )
        await repo.refresh(new_offset_transaction)

    assert new_transaction.account_id == account_id
    assert new_offset_transaction.account_id == offset_account_id

    assert new_transaction.information.amount == round(amount, 2)
    assert new_offset_transaction.information.amount == round(expected_offset_amount, 2)

    assert type(new_transaction.information.amount) == float
    assert type(new_offset_transaction.information.amount) == float

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


@pytest.mark.parametrize(
    "account_id, offset_account_id, amount",
    [
        (1, 2, 10),
        (1, 3, 20.5),
        (1, 4, -30.5),
        (1, 2, -40.5),
        (1, 2, 5.9999999999),
        (1, 2, 1.00000000004),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_create_offset_transaction_other_account_fail(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    offset_account_id,
    amount,
):
    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        offset_account = await repo.get(models.Account, offset_account_id)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        res = await client_session_wrapper_fixture.authorized_client.post(
            endpoint,
            json={
                "account_id": account_id,
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

    assert res.status_code == 401

    assert account_balance == account_balance_after
    assert offset_account_balance == offset_account_balance_after


@pytest.mark.parametrize(
    "account_id, offset_account_id, category_id, amount",
    [
        (1, 5, 1, 2.5),
        (1, 5, 1, 0),
        (1, 5, 2, 3.666666666667),
        (1, 5, 3, 0.133333333334),
        (1, 5, 4, -25),
        (1, 5, 1, -35),
        (1, 5, 1, -0.3333333334),
        (1, 5, 7, 0),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_updated_offset_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    offset_account_id,
    category_id,
    amount,
):
    async with client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        offset_account = await repo.get(models.Account, offset_account_id)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        transaction_res = await client_session_wrapper_fixture.authorized_client.post(
            endpoint,
            json={
                "account_id": account_id,
                "amount": amount + 5,
                "reference": "creation",
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": offset_account_id,
            },
        )

        transaction_before = schemas.Transaction(**transaction_res.json())

        reference = f"Offset_transaction with {amount}"
        res = await client_session_wrapper_fixture.authorized_client.post(
            f"{endpoint}{transaction_before.id}",
            json={
                "account_id": account_id,
                "amount": amount,
                "reference": reference,
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
            },
        )

        status = res.status_code
        assert status == 200

        await repo.refresh_all([account, offset_account])

    account_balance_after = account.balance
    offset_account_balance_after = offset_account.balance

    transaction = schemas.Transaction(**res.json())

    assert account_balance_after == round(account_balance + amount, 2)
    assert offset_account_balance_after == round(offset_account_balance - amount, 2)

    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.category_id == category_id


@pytest.mark.parametrize(
    "account_id, offset_account_id, category_id, amount",
    [
        (1, 5, 1, 2.5),
        (1, 5, 1, 0),
        (1, 5, 2, 3.666666666667),
        (1, 5, 3, 0.133333333334),
        (1, 5, 4, -25),
        (1, 5, 1, -35),
        (1, 5, 1, -0.3333333334),
        (1, 5, 7, 0),
    ],
)
@pytest.mark.usefixtures("test_accounts")
async def test_delete_offset_transaction(
    client_session_wrapper_fixture: ClientSessionWrapper,
    account_id,
    offset_account_id,
    category_id,
    amount,
):
    async with client_session_wrapper_fixture.client_session_wrapper_fixture.session:
        account = await repo.get(models.Account, account_id)
        offset_account = await repo.get(models.Account, offset_account_id)

        account_balance = account.balance
        offset_account_balance = offset_account.balance

        transaction_res = await client_session_wrapper_fixture.client_session_wrapper_fixture.authorized_client.post(
            endpoint,
            json={
                "account_id": account_id,
                "amount": amount,
                "reference": "creation",
                "date": str(datetime.datetime.now(datetime.timezone.utc)),
                "category_id": category_id,
                "offset_account_id": offset_account_id,
            },
        )

        transaction = schemas.Transaction(**transaction_res.json())

        res = await client_session_wrapper_fixture.client_session_wrapper_fixture.authorized_client.delete(
            f"{endpoint}{transaction.id}"
        )
        offset_transaction_res = await client_session_wrapper_fixture.client_session_wrapper_fixture.authorized_client.get(
            f"{endpoint}{transaction.offset_transactions_id}"
        )

        assert res.status_code == 204
        assert offset_transaction_res.status_code == 404

        await repo.refresh_all([account, offset_account])

    assert offset_account_balance == offset_account.balance
    assert account_balance == account.balance
