import datetime
import pytest

from app import schemas, repository as repo

#
# use with: pytest --disable-warnings -v -x
#


@pytest.mark.parametrize(
    "account_id, amount, expected_amount, reference, subcategory_id, status_code",
    [
        (1, 10, 10, "Added 10", 1, 201),
        (1, 20.5, 20.5, "Added 20.5", 3, 201),
        (1, -30.5, -30.5, "Substract 30.5", 6, 201),
        (1, -40.5, -40.5, "Subsctract 40.5", 6, 201),
    ],
)
def test_create_transaction(
    authorized_client,
    test_account,
    account_id,
    amount,
    expected_amount,
    reference,
    subcategory_id,
    status_code,
):
    res = authorized_client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
        },
    )
    new_transaction = schemas.Transaction(**res.json())

    assert res.status_code == status_code
    assert new_transaction.account_id == account_id
    assert new_transaction.information.amount == expected_amount
    assert type(new_transaction.information.amount) == float
    assert new_transaction.information.reference == reference


@pytest.mark.parametrize(
    "account_id, transaction_id, subcategory_id, amount, status_code",
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
def test_updated_transaction(
    authorized_client,
    test_transactions,
    account_id,
    transaction_id,
    subcategory_id,
    amount,
    status_code,
):
    reference = f"Updated Val {amount}"

    json = {
        "account_id": account_id,
        "amount": amount,
        "reference": f"Updated Val {amount}",
        "date": str(datetime.datetime.utcnow()),
        "subcategory_id": subcategory_id,
    }

    account_before_res = authorized_client.get(f"/accounts/{account_id}")
    account_before = schemas.Account(**account_before_res.json())

    transaction_res = authorized_client.get(f"/transactions/{transaction_id}")
    transaction_before = schemas.Transaction(**transaction_res.json())

    res = authorized_client.post(f"/transactions/{transaction_id}", json=json)

    assert res.status_code == status_code

    account_after_res = authorized_client.get(f"/accounts/{account_id}")
    account_after = schemas.Account(**account_after_res.json())

    transaction = schemas.Transaction(**res.json())

    difference = transaction_before.information.amount - amount

    assert account_after.balance == round(account_before.balance - difference, 2)
    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.subcategory_id == subcategory_id


@pytest.mark.parametrize(
    "account_id, transaction_id, status_code",
    [
        (1, 1, 204),
        (1, 2, 204),
        (1, 3, 204),
        (1, 9999, 404),
    ],
)
def test_delete_transaction(
    authorized_client, test_transactions, account_id, transaction_id, status_code
):
    account_before_res = authorized_client.get(f"/accounts/{account_id}")
    account_before = schemas.Account(**account_before_res.json())

    transaction_response = authorized_client.get(f"/transactions/{transaction_id}")

    if transaction_response.status_code == 404:
        return

    res = authorized_client.delete(f"/transactions/{transaction_id}")

    account_after_res = authorized_client.get(f"/accounts/{account_id}")
    account_after = schemas.Account(**account_after_res.json())
    new_balance = account_after.balance

    transaction = schemas.Transaction(**transaction_response.json())
    assert res.status_code == status_code
    assert new_balance == (account_before.balance - transaction.information.amount)


@pytest.mark.parametrize(
    "account_id, offset_account_id, amount, expected_offset_amount, reference, subcategory_id, status_code",
    [
        (1, 5, 10, -10, "Added 10", 1, 201),
        (1, 5, 20.5, -20.5, "Added 20.5", 3, 201),
        (1, 5, -30.5, 30.5, "Substract 30.5", 6, 201),
        (1, 5, -40.5, 40.5, "Substract 40.5", 6, 201),
        (1, 5, 5.9999999999, -6, "Added 6", 6, 201),
        (1, 5, 1.00000000004, -1, "Added 1", 6, 201),
    ],
)
def test_create_offset_transaction(
    authorized_client,
    test_accounts,
    account_id,
    offset_account_id,
    amount,
    expected_offset_amount,
    reference,
    subcategory_id,
    status_code,
):
    res = authorized_client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
            "offset_account_id": offset_account_id,
        },
    )

    assert res.status_code == status_code

    new_transaction = schemas.Transaction(**res.json())
    offset_transactions_id = new_transaction.offset_transactions_id
    res_offset = authorized_client.get(f"/transactions/{offset_transactions_id}")
    assert res_offset.status_code == 200

    new_offset_transaction = schemas.Transaction(**res_offset.json())

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
def test_create_offset_transaction_other_account_fail(
    authorized_client,
    test_accounts,
    account_id,
    offset_account_id,
    amount,
    subcategory_id,
):
    account_before = repo.get("Account", account_id)
    offset_account_before = repo.get("Account", offset_account_id)

    res = authorized_client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": "Not allowed",
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
            "offset_account_id": offset_account_id,
        },
    )

    account_after = repo.get("Account", account_id)
    offset_account_after = repo.get("Account", offset_account_id)

    assert res.status_code == 401

    assert account_before.balance == account_after.balance
    assert offset_account_before.balance == offset_account_after.balance


@pytest.mark.parametrize(
    "account_id, offset_account_id, subcategory_id, amount",
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
def test_updated_offset_transaction(
    authorized_client,
    test_accounts,
    account_id,
    offset_account_id,
    subcategory_id,
    amount,
):

    account_before_res = authorized_client.get(f"/accounts/{account_id}")
    account_before = schemas.Account(**account_before_res.json())

    offset_account_before_res = authorized_client.get(f"/accounts/{offset_account_id}")
    offset_account_before = schemas.Account(**offset_account_before_res.json())

    transaction_res = authorized_client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "amount": 10,
            "reference": "creation",
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
            "offset_account_id": offset_account_id,
        },
    )
    assert transaction_res.status_code == 201

    transaction_before = schemas.Transaction(**transaction_res.json())

    reference = f"Offset_transaction with {amount}"
    res = authorized_client.post(
        f"/transactions/{transaction_before.id}",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": reference,
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
        },
    )
    assert res.status_code == 200

    account_after_res = authorized_client.get(f"/accounts/{account_id}")
    account_after = schemas.Account(**account_after_res.json())

    offset_account_after_res = authorized_client.get(f"/accounts/{offset_account_id}")
    offset_account_after = schemas.Account(**offset_account_after_res.json())

    transaction = schemas.Transaction(**res.json())

    assert account_after.balance == round(account_before.balance + amount, 2)
    assert offset_account_after.balance == round(
        offset_account_before.balance - amount, 2
    )

    assert transaction.information.amount == round(amount, 2)
    assert transaction.information.reference == reference
    assert transaction.information.subcategory_id == subcategory_id


@pytest.mark.parametrize(
    "account_id, offset_account_id, subcategory_id, amount",
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
def test_delete_offset_transaction(
    authorized_client,
    test_accounts,
    account_id,
    offset_account_id,
    subcategory_id,
    amount,
):

    account_before_res = authorized_client.get(f"/accounts/{account_id}")
    account_before = schemas.Account(**account_before_res.json())

    offset_account_before_res = authorized_client.get(f"/accounts/{offset_account_id}")
    offset_account_before = schemas.Account(**offset_account_before_res.json())

    transaction_res = authorized_client.post(
        "/transactions/",
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": "creation",
            "date": str(datetime.datetime.utcnow()),
            "subcategory_id": subcategory_id,
            "offset_account_id": offset_account_id,
        },
    )

    transaction = schemas.Transaction(**transaction_res.json())

    res = authorized_client.delete(f"/transactions/{transaction.id}")
    offset_transaction_res = authorized_client.get(
        f"/transactions/{transaction.offset_transactions_id}"
    )

    assert res.status_code == 204
    assert offset_transaction_res.status_code == 404

    account_after_res = authorized_client.get(f"/accounts/{account_id}")
    account_after = schemas.Account(**account_after_res.json())

    offset_account_after_res = authorized_client.get(f"/accounts/{offset_account_id}")
    offset_account_after = schemas.Account(**offset_account_after_res.json())

    assert offset_account_before.balance == offset_account_after.balance
    assert account_before.balance == account_after.balance
