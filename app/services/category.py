from typing import Optional

from app import models
from app.exceptions.base_service_exception import EntityAccessDeniedException
from app.services.base import BaseService


class CategoryService(BaseService):

    async def get_categories(
        self,
        _current_user: models.User,
    ) -> Optional[list[models.TransactionCategory]]:
        """
        Retrieves a list of transaction categories.

        Args:
            current_user: The current active user.

        Returns:
            list[TransactionCategory]: A list of transaction category objects.
        """

        return await self.repository.get_all(models.TransactionCategory)

    async def get_category(
        self, user: models.User, category_id: int
    ) -> models.TransactionCategory:
        """
        Retrieves a transaction category by ID.

        Args:
            current_user: The current active user.
            category_id: The ID of the transaction category to retrieve.

        Returns:
            TransactionCategory: The retrieved transaction category.

        Raises:
            EntityAccessDeniedException: If the user does not have access to the category.
        """

        category = await self.repository.get(models.TransactionCategory, category_id)

        if category.user_id == user.id:
            raise EntityAccessDeniedException(user, category)

        return category

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
