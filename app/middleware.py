from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class HeaderLinkMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.header_links = [
            {"url": "/about", "text": "About Us"},
            {"url": "/contact", "text": "Contact Us"},
        ]
        return await call_next(request)
