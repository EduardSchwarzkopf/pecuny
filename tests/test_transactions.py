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
    assert type(new_transaction.information.id) == int
