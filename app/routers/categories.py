from typing import List
from fastapi import Depends, APIRouter, status, Response
from fastapi.exceptions import HTTPException

from .. import schemas, transaction_manager as tm
from ..services import categories as service
from app.routers.users import current_active_user
from app.database import User

router = APIRouter()
response_model = schemas.CategoryData


@router.get("/", response_model=List[response_model])
async def get_categories(current_user: User = Depends(current_active_user)):
    return await service.get_categories(current_user)


@router.get("/{category_id}", response_model=response_model)
async def get_category(
    category_id: int, current_user: User = Depends(current_active_user)
):
    category = await service.get_category(current_user, category_id)

    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Category not found")

    return category


# @router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
# async def create_category(
#     category: schemas.category, current_user: User = Depends(current_active_user)
# ):
#     category = await tm.transaction(service.create_category, current_user, category)
#     return category


# @router.put("/{category_id}", response_model=response_model)
# async def update_category(
#     category_id: int,
#     category_data: schemas.categoryUpdate,
#     current_user: User = Depends(current_active_user),
# ):
#     return await tm.transaction(
#         service.update_category, current_user, category_id, category_data
#     )


# @router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_category(
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
