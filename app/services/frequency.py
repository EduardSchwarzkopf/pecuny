from app import models
from app.services.base import BaseService


class FrequencyService(BaseService):

    async def get_frequency_list(
        self,
    ) -> list[models.TransactionCategory]:
        """
        Get a list of transaction categories based on frequency.

        Returns:
            Optional[list[models.TransactionCategory]]:
                A list of transaction categories based on frequency,
                or None if not found.
        """

        return await self.repository.get_all(models.Frequency)

    async def get_frequency(self, frequency_id: int) -> models.Frequency:
        """
        Get a specific transaction category by frequency ID.

        Args:
            frequency_id (int): The ID of the frequency to retrieve.

        Returns:
            Optional[models.Frequency]: The transaction category corresponding
                 to the given frequency ID, or None if not found.
        """

        return await self.repository.get(models.Frequency, frequency_id)
