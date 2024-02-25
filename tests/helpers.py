import asyncio
from typing import List

from fastapi import Response
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.repository import ModelT
from app.utils.dataclasses_utils import ClientSessionWrapper
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


async def fixture_cleanup(session: AsyncSession, object_list: List[ModelT]) -> None:

    delete_task = [session.delete(object) for object in object_list]

    await asyncio.gather(*delete_task)

    await session.commit()
