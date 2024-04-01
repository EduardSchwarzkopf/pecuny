import pytest
from starlette.status import HTTP_204_NO_CONTENT, HTTP_403_FORBIDDEN

from app import models
from app import repository as repo
from app.utils.enums import DatabaseFilterOperator, RequestMethod
from tests.utils import make_http_request


@pytest.mark.parametrize(
    "values",
    [
        ({"email": "mewmew.de"}),
        ({"password": ""}),
        ({"is_superuser": True}),
        ({"email": "anothermail.com"}),
    ],
)
async def test_invalid_updated_user(test_user: models.User, values: dict):
    """
    Test case for updating a user with invalid values.

    Args:
        test_user (fixture): The test user.
        values (dict): The updated values for the user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.

    """

    user_id = str(test_user.id)
    res = await make_http_request(
        f"/api/users/{user_id}",
        json=values,
        method=RequestMethod.PATCH,
        as_user=test_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN


async def test_delete_user(
    test_user: models.User,
):
    """
    Test case for deleting a user.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    res = await make_http_request(
        "/api/users/me", method=RequestMethod.DELETE, as_user=test_user
    )

    assert res.status_code == HTTP_204_NO_CONTENT

    user = await repo.get(models.User, test_user.id)
    assert user is None


async def test_invalid_delete_user(test_user: models.User):
    """
    Test case for deleting a user.

    Args:
        test_user (fixture): The test user.

    Returns:
        None

    Raises:
        AssertionError: If the test fails.
    """
    other_user_list = await repo.filter_by_multiple(
        models.User,
        [
            (models.User.email, test_user.email, DatabaseFilterOperator.NOT_EQUAL),
            (models.User.is_verified, True, DatabaseFilterOperator.EQUAL),
        ],
    )
    other_user = other_user_list[-1]
    res = await make_http_request(
        url=f"/api/users/{other_user.id}",
        method=RequestMethod.DELETE,
        as_user=test_user,
    )

    assert res.status_code == HTTP_403_FORBIDDEN
