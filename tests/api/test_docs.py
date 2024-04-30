from app.utils.enums import RequestMethod
from tests.utils import make_http_request


async def test_docs_response():
    response = await make_http_request("/openapi.json", method=RequestMethod.GET)
    assert response.status_code == 200
