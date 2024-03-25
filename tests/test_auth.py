from httpx import Cookies

from app import models
from app.auth_manager import get_strategy
from app.config import settings
from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_refresh_token_handling(test_user: models.User):

    strategy = get_strategy()
    token = await strategy.write_refresh_token(test_user)

    cookies = Cookies(
        {
            settings.refresh_token_name: token,
        }
    )

    endpoint = "/api/users/me"

    res = await make_http_request(
        url=endpoint, method=RequestMethod.GET, cookies=cookies
    )
    assert res.status_code == 200
