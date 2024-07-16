from io import BufferedReader
from typing import Optional

from fastapi import Response
from httpx import AsyncClient, Cookies, QueryParams

from app import models
from app.auth_manager import get_strategy
from app.config import settings
from app.main import app
from app.repository import Repository
from app.utils.enums import DatabaseFilterOperator, RequestMethod


async def authorized_httpx_client(client: AsyncClient, user: models.User):
    """
    Fixture that provides an authorized client with a token.

    Args:
        client: The async client fixture.
        token: The authentication token.

    Returns:
        AsyncClient: An authorized client with the provided token.
    """

    strategy = get_strategy()
    token = await strategy.write_token(user)

    client.cookies = {
        **client.cookies,
        settings.access_token_name: token,
    }
    return client


async def make_http_request(  # pylint: disable=too-many-arguments
    url: str,
    data: Optional[dict] = None,
    json: Optional[dict] = None,
    as_user: Optional[models.User] = None,
    method: RequestMethod = RequestMethod.POST,
    cookies: Optional[Cookies] = None,
    params: Optional[QueryParams] = None,
    files: Optional[dict[str, tuple[str, BufferedReader, str]]] = None,
) -> Response:
    """
    Makes an HTTP request to the specified URL using the given method and JSON data.

    Args:
        url: The URL to make the request to.
        json: The JSON data to include in the request body. Defaults to None.
        as_user: The user to authorize the request as. Defaults to None.
        method: The HTTP method to use for the request.
        cookies: Cookies to include in the request. Defaults to None.
        params: Query parameters to include in the request. Defaults to None.
        files: Files to upload with the request. Defaults to None.

    Returns:
        Response: The response object.

    Raises:
        ValueError: If an invalid method is provided.
    """

    async with AsyncClient(app=app, base_url="http://test") as client:

        if cookies:
            client.cookies = {**client.cookies, **cookies}

        if as_user:
            client = await authorized_httpx_client(client, as_user)

        if method == RequestMethod.POST:
            response = client.post(url, json=json, data=data, files=files)
        elif method == RequestMethod.PATCH:
            response = client.patch(url, json=json, data=data, files=files)
        elif method == RequestMethod.GET:
            response = client.get(url, params=params)
        elif method == RequestMethod.DELETE:
            response = client.delete(url)
        else:
            raise ValueError(
                f"Invalid method: {method}. Expected one of: get, post, patch, delete."
            )

        return await response


async def get_user_offset_account(
    account: models.Account, repository: Repository
) -> Optional[models.Account]:
    """
    Returns the offset account for a given account within a list of accounts.

    Args:
        account (models.Account): The account for which to find the offset account.
        account_list (list[models.Account]): The list of accounts to search within.

    Returns:
        models.Account or None: The offset account if found, otherwise None.
    """

    account_list = await repository.filter_by_multiple(
        models.Account,
        [
            (
                models.Account.user_id,
                account.user.id,
                DatabaseFilterOperator.EQUAL,
            ),
            (
                models.Account.id,
                account.id,
                DatabaseFilterOperator.NOT_EQUAL,
            ),
        ],
    )

    if account_list is None:
        raise ValueError("No accounts found")

    return account_list[0]


async def get_other_user_account(
    user: models.User, repository: Repository
) -> Optional[models.Account]:

    account_list = await repository.filter_by(
        models.Account,
        models.Account.user_id,
        user.id,
        DatabaseFilterOperator.NOT_EQUAL,
    )

    if account_list is None:
        raise ValueError("No accounts found")

    return account_list[0]
