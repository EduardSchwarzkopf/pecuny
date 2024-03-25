from typing import Optional

from fastapi import Response
from httpx import AsyncClient, Cookies

from app import models, repository
from app.auth_manager import get_strategy
from app.config import settings
from app.main import app
from app.utils.enums import RequestMethod


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
    token = strategy.write_token(user)

    client.cookies = {
        **client.cookies,
        settings.access_token_name: await token,
    }
    return client


async def make_http_request(
    url: str,
    data: Optional[dict] = None,
    json: Optional[dict] = None,
    as_user: Optional[models.User] = None,
    method: RequestMethod = RequestMethod.POST,
    cookies: Optional[Cookies] = None,
) -> Response:
    """
    Makes an HTTP request to the specified URL using the given method and JSON data.

    Args:
        client_session_wrapper: The client session wrapper object.
        method: The HTTP method to use for the request.
        url: The URL to make the request to.
        json_data: The JSON data to include in the request body. Defaults to None.

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
            response = await client.post(url, json=json, data=data)
        elif method == RequestMethod.PATCH:
            response = await client.patch(url, json=json, data=data)
        elif method == RequestMethod.GET:
            response = await client.get(url)
        elif method == RequestMethod.DELETE:
            response = await client.delete(url)
        else:
            raise ValueError(
                f"Invalid method: {method}. Expected one of: get, post, patch, delete."
            )

    return response


async def get_user_offset_account(account: models.Account) -> Optional[models.Account]:
    """
    Returns the offset account for a given account within a list of accounts.

    Args:
        account (models.Account): The account for which to find the offset account.
        account_list (list[models.Account]): The list of accounts to search within.

    Returns:
        models.Account or None: The offset account if found, otherwise None.
    """
    account_list = await repository.get_all(models.Account)
    return next(
        (
            account_element
            for account_element in account_list
            if (
                account_element.user_id == account.user_id
                and account.id != account_element.id
            )
        ),
        None,
    )
