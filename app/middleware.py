from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class HeaderLinkMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Dispatches the request to the next middleware or route handler.

        Args:
            self: The instance of the middleware.
            request (Request): The incoming request object.
            call_next (Callable): The next middleware or route handler.

        Returns:
            Awaitable: The response returned by the next middleware or route handler.
        """
        request.state.header_links = [
            # {
            #     "url": dashboard_router.prefix,
            #     "text": "Dashboard",
            #     "active": current_path.startswith(dashboard_router.prefix),
            # },
        ]
        return await call_next(request)
