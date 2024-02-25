from fastapi import Response
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.enums import RequestMethod


async def make_http_request(
    session: AsyncSession,
    client: AsyncClient,
    url: str,
    data: dict = None,
    json: dict = None,
    method: RequestMethod = RequestMethod.POST,
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

    async with session:
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


async def get_account(
    client_session_wrapper: ClientSessionWrapper, account_id: int
) -> schemas.Account:
    account_response = await make_http_request(
        client_session_wrapper.session,
        client_session_wrapper.authorized_client,
        f"/api/accounts/{account_id}",
        method=RequestMethod.GET,
    )
    return schemas.Account(**account_response.json())


async def fixture_cleanup(session: AsyncSession, object_list: List[ModelT]) -> None:
    for object in object_list:
        session.delete(object)

    await session.commit()
