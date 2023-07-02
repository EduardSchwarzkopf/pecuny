from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.routers.dashboard import router as dashboard_router


class HeaderLinkMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        current_path = request.url.path

        request.state.header_links = [
            # {
            #     "url": dashboard_router.prefix,
            #     "text": "Dashboard",
            #     "active": current_path.startswith(dashboard_router.prefix),
            # },
        ]
        return await call_next(request)
