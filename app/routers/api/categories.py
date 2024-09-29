from fastapi import Depends

from app import schemas
from app.models import User
from app.routers.api.users import current_active_verified_user
from app.services.category import CategoryService
from app.utils import APIRouterExtended

router = APIRouterExtended(prefix="/categories", tags=["Categories"])
ResponseModel = schemas.CategoryData


@router.get("/", response_model=list[ResponseModel])
async def api_get_categories(
    current_user: User = Depends(current_active_verified_user),
    service: CategoryService = Depends(CategoryService.get_instance),
):
    """
    Retrieves a category by ID.

    Args:
        category_id: The ID of the category.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved category information.
    """

    return await service.get_categories(current_user)


@router.get("/{category_id}", response_model=ResponseModel)
async def api_get_category(
    category_id: int,
    current_user: User = Depends(current_active_verified_user),
    service: CategoryService = Depends(CategoryService.get_instance),
):
    """
    Retrieves a category by ID.

    Args:
        category_id: The ID of the category.
        current_user: The current active user.

    Returns:
        ResponseModel: The retrieved category information.
    """

    return await service.get_category(current_user, category_id)


# @router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
# async def api_create_category(
#     category: schemas.category, current_user: User = Depends(current_active_user)
# ):
#     category = await tm.transaction(service.create_category, current_user, category)
#     return category


# @router.put("/{category_id}", response_model=response_model)
# async def api_update_category(
#     category_id: int,
#     category_data: schemas.categoryUpdate,
#     current_user: User = Depends(current_active_user),
# ):
#     return await tm.transaction(
#         service.update_category, current_user, category_id, category_data
#     )


# @router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def api_delete_category(
#     category_id: int, current_user: User = Depends(current_active_user)
# ):
#     result = await tm.transaction(service.delete_category, current_user, category_id)
#     if result:
#         return Response(
#             status_code=status.HTTP_204_NO_CONTENT,
#             content="category deleted successfully",
#         )

#     if result is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="category not found"
#         )
