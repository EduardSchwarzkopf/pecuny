from typing import Optional

from app import models
from app.logger import get_logger
from app.repository import Repository
from app.services.base import BaseService

logger = get_logger(__name__)


class FrequencyService(BaseService):

    def __init__(self, repository: Optional[Repository] = None):
        self.logger = logger
        super().__init__(logger, repository)

    async def get_frequency_list(
        self,
    ) -> Optional[list[models.TransactionCategory]]:
        """
        Get a list of transaction categories based on frequency.

        Returns:
            Optional[list[models.TransactionCategory]]:
                A list of transaction categories based on frequency,
                or None if not found.
        """

        return await self.repository.get_all(models.Frequency)

    async def get_frequency(self, frequency_id: int) -> Optional[models.Frequency]:
        """
        Get a specific transaction category by frequency ID.

        Args:
            frequency_id (int): The ID of the frequency to retrieve.

        Returns:
            Optional[models.Frequency]: The transaction category corresponding
                 to the given frequency ID, or None if not found.
        """

        return await self.repository.get(models.Frequency, frequency_id)
