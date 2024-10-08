import asyncio

from starlette.status import HTTP_201_CREATED

from app.date_manager import get_iso_timestring
from app.models import User, Wallet
from tests.utils import make_http_request


async def test_isolated_db_session(test_user: User, test_wallet: Wallet):
    """
    Test the isolated database session by making multiple HTTP requests to create transactions.

        Args:
            test_user (fixture): The test user object.
            test_wallet (fixture): The test wallet object.
    """

    num_of_requests = 5
    tasks = [
        asyncio.create_task(
            make_http_request(
                "/api/transactions/",
                as_user=test_user,
                json={
                    "wallet_id": test_wallet.id,
                    "amount": 100,
                    "reference": f"Test me - {i}",
                    "date": get_iso_timestring(),
                    "category_id": 1,
                },
            )
        )
        for i in range(num_of_requests)
    ]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == HTTP_201_CREATED
