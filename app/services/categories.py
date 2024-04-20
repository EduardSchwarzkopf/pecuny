from typing import Optional

from app import models
from app.logger import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class CategoryService(BaseService):

    async def get_categories(
        self,
        current_user: models.User,
    ) -> Optional[list[models.TransactionCategory]]:
        """
        Retrieves a list of transaction categories.

        Args:
            current_user: The current active user.

        Returns:
            list[TransactionCategory]: A list of transaction category objects.
        """

        logger.info("Getting categories for user %s", current_user.id)
        return await self.repository.get_all(models.TransactionCategory)

    async def get_category(
        self, current_user: models.User, category_id: int
    ) -> Optional[models.TransactionCategory]:
        """
        Retrieves a transaction category by ID.

        Args:
            current_user: The current active user.
            category_id: The ID of the transaction category to retrieve.

        Returns:
            TransactionCategory: The retrieved transaction category.

        Raises:
            None
        """

        logger.info(
            "Getting category with id %s for user %s", category_id, current_user.id
        )
        category = await self.repository.get(models.TransactionCategory, category_id)

        if category and (
            category.user_id is None or category.user_id == current_user.id
        ):
            return category

        logger.info(
            "Category with id %s does not belong to user %s or does not exist",
            category_id,
            current_user.id,
        )
        return None

    # async def create_category(
    #     user: models.User, category: schemas.TransactionCategory
    # ) -> models.TransactionCategory:

    #     db_category = models.TransactionCategory(user=user, **category.dict())
    #     await repo.save(db_category)
    #     return db_category

    # async def update_category(
    #     current_user: models.User, category_id, category: schemas.TransactionCategoryData
    # ) -> models.TransactionCategory:

    #     db_category = await repo.get(models.TransactionCategory, category_id)
    #     if db_category.user_id == current_user.id:
    #         await repo.update(models.TransactionCategory, db_category.id, **category.dict())
    #         return db_category

    #     return None

    # async def delete_category(current_user: models.User, category_id: int) -> bool:

    #     category = await repo.get(models.TransactionCategory, category_id)
    #     if category and category.user_id == current_user.id:
    #         await repo.delete(category)
    #         return True

    #     return None
