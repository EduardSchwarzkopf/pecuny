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


async def get_user_offset_wallet(
    wallet: models.Wallet, repository: Repository
) -> Optional[models.Wallet]:
    """
    Returns the offset wallet for a given wallet within a list of wallets.

    Args:
        wallet (models.Wallet): The wallet for which to find the offset wallet.
        repository (Repository): The repository to query for wallet information.

    Returns:
        models.Wallet or None: The offset wallet if found, otherwise None.
    """

    wallet_list = await repository.filter_by_multiple(
        models.Wallet,
        [
            (
                models.Wallet.user_id,
                wallet.user.id,
                DatabaseFilterOperator.EQUAL,
            ),
            (
                models.Wallet.id,
                wallet.id,
                DatabaseFilterOperator.NOT_EQUAL,
            ),
        ],
    )

    if wallet_list is None:
        raise ValueError("No wallets found")

    return wallet_list[0]


async def get_other_user_wallet(
    user: models.User, repository: Repository
) -> models.Wallet:
    """
    Returns an wallet belonging to a user other than the specified user.

    Args:
        user: The user for whom to find another wallet.
        repository: The repository to query for wallet information.

    Returns:
        models.Wallet: An wallet belonging to a user other than the specified user.

    Raises:
        ValueError: If no wallets are found for the user.
    """

    wallet_list = await repository.filter_by(
        models.Wallet,
        models.Wallet.user_id,
        user.id,
        DatabaseFilterOperator.NOT_EQUAL,
    )

    if wallet_list is None:
        raise ValueError("No wallets found")

    return wallet_list[0]
