from typing import Optional

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
from app.services.users import UserService
from app.utils.enums import RequestMethod
from tests.utils import make_http_request

value_list = [
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


async def update_user_test(
    test_user: models.User, values: dict, user_service: UserService
) -> None:
    """
    Test case for updating a user's information.

    Args:
        test_user: The user whose information is being updated.
        values: Dictionary of values to update the user with.
        user_service: The UserService instance for managing users.

    Returns:
        None
    """

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
            db_user: models.User = await user_service.user_manager.get(test_user.id)
            assert db_user.is_verified is False

        assert getattr(user, key) == value


@pytest.mark.parametrize("values", value_list)
async def test_update_active_verified_user_self(
    user_service: UserService, active_verified_user: models.User, values: dict
):
    """
    Test case for updating a user.

    Args:
        active_verified_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    await update_user_test(active_verified_user, values, user_service)


@pytest.mark.parametrize("values", value_list)
async def test_update_active_user_self(
    user_service: UserService, active_user: models.User, values: dict
):
    """
    Test case for updating a user.

    Args:
        active_verified_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """

    await update_user_test(active_user, values, user_service)


@pytest.mark.parametrize("values", value_list)
async def test_invalid_update_inactive_user_self(
    inactive_user: models.User, values: dict
) -> None:
    """
    Test case for attempting to update an inactive user's own information.

    Args:
        inactive_user: The inactive user attempting to update their own information.
        values: Dictionary of values for the update attempt.

    Returns:
        None
    """

    res = await make_http_request(
        "/api/users/me",
        json=values,
        method=RequestMethod.PATCH,
        as_user=inactive_user,
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
    active_verified_user: models.User, test_user: models.User, values: dict
):
    """
    Test case for attempting to update a user with invalid values.

    Args:
        active_verified_user:
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
        as_user=active_verified_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN


async def test_delete_self(
    active_verified_user: models.User,
):
    """
    Test case for deleting a user.

    Args:
        active_verified_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    res = await make_http_request(
        "/api/users/me", method=RequestMethod.DELETE, as_user=active_verified_user
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    user = await repo.get(models.User, active_verified_user.id)
    assert user is None


async def test_invalid_delete_other_user(
    active_verified_user: models.User, test_user: models.User
):
    """
    Test case for attempting to delete another user without sufficient permissions.

    Args:
        active_verified_user (fixture):
            The active and verified user performing the delete operation.
        test_user (fixture): The user to be deleted.

    Returns:
        None
    """

    res = await make_http_request(
        url=f"/api/users/{test_user.id}",
        method=RequestMethod.DELETE,
        as_user=active_verified_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN

    refresh_user: Optional[models.User] = await repo.get(models.User, test_user.id)

    assert refresh_user is not None

    assert test_user.displayname == refresh_user.displayname
    assert test_user.email == refresh_user.email
    assert refresh_user.is_active is True
    assert refresh_user.is_verified is True
    assert refresh_user.is_superuser is False


async def test_update_email(
    active_verified_user: models.User, user_service: UserService
):
    """
    Test case for updating the email of a user.

    Args:
        active_verified_user: The active and verified user whose email is being updated.
        user_service: The UserService instance for managing users.

    Returns:
        None
    """

    res = await make_http_request(
        "/api/users/me",
        json={"email": "newmail@example.com"},
        method=RequestMethod.PATCH,
        as_user=active_verified_user,
    )

    assert res.status_code == HTTP_200_OK

    manager = user_service.user_manager
    user = await manager.get(active_verified_user.id)

    assert user.is_active is True
    assert user.is_verified is False

    token = user_service.user_manager.get_token(active_verified_user)

    verify_response = await make_http_request(
        "/api/auth/verify",
        method=RequestMethod.POST,
        as_user=active_verified_user,
        json={"token": token},
    )

    verify_response.status_code == HTTP_200_OK  # pylint: disable=pointless-statement

    verified_user = await manager.get(active_verified_user.id)

    assert verified_user.is_active is True
    assert verified_user.is_verified is True
