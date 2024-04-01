import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from app import models
from app import repository as repo
from app import schemas
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

values = [
    ({"email": "mew@mew.de"}),
    ({"displayname": "Agent Smith"}),
    ({"password": "lancelot"}),
    (
        {
            "displayname": "Agent Test",
            "email": "user@example.com",
            "password": "password123",
        }
    ),
]


async def update_user_test(test_user: models.User, values: dict) -> None:

    res = await make_http_request(
        "/api/users/me",
        json=values,
        method=RequestMethod.PATCH,
        as_user=test_user,
    )

    assert res.status_code == HTTP_200_OK
    user = schemas.UserRead(**res.json())

    for key, value in values.items():
        if key == "password":
            login_res = await make_http_request(
                "/api/auth/login",
                {"username": user.email, "password": value},
            )
            assert login_res.status_code == HTTP_204_NO_CONTENT
            continue

        if key == "email":
            db_user: models.User = await repo.get(models.User, test_user.id)
            assert db_user.is_verified == False

        assert getattr(user, key) == value


@pytest.mark.parametrize("values", values)
async def test_update_active_verified_user_self(
    test_active_verified_user: models.User, values: dict
):
    """
    Test case for updating a user.

    Args:
        test_active_verified_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    update_user_test(test_active_verified_user, values)


@pytest.mark.parametrize("values", values)
async def test_update_active_user_self(test_active_user: models.User, values: dict):
    """
    Test case for updating a user.

    Args:
        test_active_verified_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    update_user_test(test_active_user, values)


@pytest.mark.parametrize("values", values)
async def test_invalid_update_inactive_user_self(
    test_inactive_user: models.User, values: dict
) -> None:

    res = await make_http_request(
        "/api/users/me",
        json=values,
        method=RequestMethod.PATCH,
        as_user=test_inactive_user,
    )

    assert res.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mewmew.de"}),
        ({"password": ""}),
        ({"is_superuser": True}),
        ({"email": "anothermail.com"}),
    ],
)
async def test_invalid_updated_user(
    test_active_verified_user: models.User, test_user: models.User, values: dict
):
    """
    Test case for attempting to update a user with invalid values.

    Args:
        test_active_verified_user:
            The active and verified user performing the update operation.
        test_user: The user to be updated.
        values: Dictionary of invalid values to update the user with.

    Returns:
        None
    """

    user_id = str(test_user.id)
    res = await make_http_request(
        f"/api/users/{user_id}",
        json=values,
        method=RequestMethod.PATCH,
        as_user=test_active_verified_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN


async def test_delete_self(
    test_active_verified_user: models.User,
):
    """
    Test case for deleting a user.

    Args:
        test_active_verified_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    res = await make_http_request(
        "/api/users/me", method=RequestMethod.DELETE, as_user=test_active_verified_user
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    user = await repo.get(models.User, test_active_verified_user.id)
    assert user is None


async def test_invalid_delete_other_user(
    test_active_verified_user: models.User, test_user: models.User
):
    """
    Test case for attempting to delete another user without sufficient permissions.

    Args:
        test_active_verified_user (fixture):
            The active and verified user performing the delete operation.
        test_user (fixture): The user to be deleted.

    Returns:
        None
    """

    res = await make_http_request(
        url=f"/api/users/{test_user.id}",
        method=RequestMethod.DELETE,
        as_user=test_active_verified_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN

    refresh_user: models.User = await repo.get(models.User, test_user.id)

    assert refresh_user is not None

    assert test_user.displayname == refresh_user.displayname
    assert test_user.email == refresh_user.email
    assert refresh_user.is_active is True
    assert refresh_user.is_verified is True
    assert refresh_user.is_superuser is False
