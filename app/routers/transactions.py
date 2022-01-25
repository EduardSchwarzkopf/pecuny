from typing import List
from fastapi import Depends, APIRouter, status
from fastapi.exceptions import HTTPException
from .. import models, schemas, oauth2
from ..transaction_manager import transaction as tm
from ..services import transactions as service

router = APIRouter(prefix="/transactions", tags=["Transactions"])
response_model = schemas.Transaction


@router.get("/{id}", response_model=List[response_model])
def get_transactions(
    current_user: models.User = Depends(oauth2.get_current_user),
):
    transactions = service.get(current_user)
    return transactions


@router.post("/", reponse_model=response_model)
def create_transaction(
    current_user: models.User = Depends(oauth2.get_current_user),
):
    transaction = tm.transaction(service.create, data)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"transaction with id: {id} was not found",
        )

    return transaction


@router.put("/{id}", response_model=response_model)
def update_transaction(
    current_user: models.User = Depends(oauth2.get_current_user),
):
    transaction = tm.transaction(service.update, data)
    json = mapper.to_json(transaction)
    response = arh.response(data=json)
    return response


@router.delete("/delete/{id}", status=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    result = tm.transaction(service.delete, data)
    response = arh.response(result)
    return response
