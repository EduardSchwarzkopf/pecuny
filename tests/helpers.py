from typing import Literal

from fastapi import Response

from app.utils.dataclasses_utils import ClientSessionWrapper

_MethodName = Literal["get", "post", "patch", "delete"]


async def make_http_request(
    client_session_wrapper: ClientSessionWrapper,
    url: str,
    json_data: dict = None,
    method: _MethodName = "post",
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

    async with client_session_wrapper.session:
        if method.lower() == "post":
            response = await client_session_wrapper.client.post(url, json=json_data)
        elif method.lower() == "patch":
            response = await client_session_wrapper.client.patch(url, json=json_data)
        elif method.lower() == "get":
            response = await client_session_wrapper.client.get(url)
        elif method.lower() == "delete":
            response = await client_session_wrapper.client.delete(url)
        else:
            raise ValueError(
                f"Invalid method: {method}. Expected one of: get, post, patch, delete."
            )

    return response
