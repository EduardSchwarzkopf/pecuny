import datetime
import pytest
from jose import jwt

from app import schemas
from app.config import settings

#
# use with: pytest --disable-warnings -v -x
#


@pytest.mark.parametrize(
    "account_id, amount, expected_amount, reference, subcategory_id, status_code",
    [
        (1, 10, 10, "Added 10", 1, 201),
        (1, 20.5, 20.5, "Added 20.5", 3, 201),
        (1, -30.5, -30.5, "Substract 30.5", 6, 201),
        (1, 40.5, -40.5, "Subsctract 40.5", 6, 201),
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
    "account_id, offset_account_id, amount, expected_amount, reference, subcategory_id, status_code",
    [
        (1, 5, 10, 10, "Added 10", 1, 201),
        (1, 5, 20.5, 20.5, "Added 20.5", 3, 201),
        (1, 5, -30.5, -30.5, "Substract 30.5", 6, 201),
        (1, 5, 40.5, -40.5, "Subsctract 40.5", 6, 201),
    ],
)
def test_create_offset_transaction(
    authorized_client,
    test_accounts,
    account_id,
    offset_account_id,
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
            "offset_account_id": offset_account_id,
        },
    )

    new_transaction = schemas.Transaction(**res.json())

    offset_transactions_id = new_transaction.offset_transactions_id

    res_offset = authorized_client.get(f"/transactions/{offset_transactions_id}")

    assert res_offset.status_code == 200
    new_offset_transaction = schemas.Transaction(**res_offset.json())

    assert res.status_code == status_code
    assert new_transaction.account_id == account_id
    assert new_offset_transaction.account_id == offset_account_id

    assert new_transaction.information.amount == expected_amount
    assert (
        new_transaction.information.amount
        == new_offset_transaction.information.amount * -1
    )

    assert type(new_transaction.information.amount) == float
    assert type(new_offset_transaction.information.amount) == float

    assert new_transaction.information.reference == reference
    assert new_offset_transaction.information.reference == reference


# check if offset transaction can pull money from an account, that the user does not own
def test_create_offset_transaction_other_account_fail(
    authorized_client, test_transactions
):
    pass


def test_edit_offset_transaction(authorized_client, test_transactions):
    pass
