import pytest

from app import schemas
from app.utils.dataclasses_utils import ClientSessionWrapper

pytestmark = pytest.mark.anyio
ENDPOINT = "/api/accounts/"


async def test_create_account(client_session_wrapper: ClientSessionWrapper):
    """
    Tests the create account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={"label": "test_account", "description": "test", "balance": 500},
        )

    assert res.status_code == 201

    new_account = schemas.Account(**res.json())

    assert new_account.label == "test_account"
    assert new_account.balance == 500
    assert new_account.description == "test"


@pytest.mark.parametrize(
    "label, description, balance",
    [
        ("", None, None),
        ("test", "test", "aaaa"),
        ("test", "test", "0,3"),
    ],
)
async def test_invalid_create_account(
    client_session_wrapper: ClientSessionWrapper, label, description, balance
):
    """
    Tests the delete account functionality.

    Args:
        authorized_client: The authorized client fixture.
        account_id (str): The ID of the account to delete.
        status_code (int): The expected status code.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.post(
            ENDPOINT,
            json={"label": label, "description": description, "balance": balance},
        )

    assert res.status_code == 422


@pytest.mark.usefixtures("test_account")
async def test_delete_account(client_session_wrapper: ClientSessionWrapper):
    """
    Tests the update account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    res = await client_session_wrapper.authorized_client.delete(f"{ENDPOINT}1")

    assert res.status_code == 204


@pytest.mark.parametrize(
    "account_id, status_code",
    [("2", 404), ("3", 404), ("4", 404), ("999999", 404)],
)
@pytest.mark.usefixtures("test_account")
async def test_invalid_delete_account(
    client_session_wrapper: ClientSessionWrapper, account_id, status_code
):
    """
    Tests the update account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    res = await client_session_wrapper.authorized_client.delete(
        f"{ENDPOINT}{account_id}"
    )

    assert res.status_code == status_code


@pytest.mark.parametrize(
    "values",
    [
        (
            {
                "label": "My new Label",
                "description": "very new description",
                "balance": 1111.3,
            }
        ),
        (
            {
                "label": "11113",
                "description": "cool story bro '",
                "balance": 2000,
            }
        ),
        (
            {
                "label": "My new Label",
                "description": "very new description",
                "balance": -0.333333334,
            }
        ),
        (
            {
                "label": "My new Label",
                "description": "very new description",
                "balance": -1000000.3,
            }
        ),
    ],
)
@pytest.mark.usefixtures("test_account")
async def test_update_account(client_session_wrapper: ClientSessionWrapper, values):
    """
    Tests the update account functionality.

    Args:
        session: The session fixture.
        authorized_client: The authorized client fixture.
        values: The values to update the account with.

    Returns:
        None
    """

    async with client_session_wrapper.session:
        res = await client_session_wrapper.authorized_client.put(
            f"{ENDPOINT}1", json=values
        )

    assert res.status_code == 200
    account = schemas.AccountData(**res.json())

    for key, value in values.items():
        if key == "id":
            continue

        account_val = getattr(account, key)
        print(f"key: {key} | value: {value} | account_val: {account_val}")
        if isinstance(value, str):
            assert account_val == value
        else:
            assert account_val == round(value, 2)
