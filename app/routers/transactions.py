from typing import List
from fastapi import Depends, APIRouter, status
from fastapi.exceptions import HTTPException
from .. import models, schemas, oauth2, transaction_manager as tm
from ..services import transactions as service

router = APIRouter(prefix="/transactions", tags=["Transactions"])
response_model = schemas.Transaction


# @router.get("/{id}", response_model=List[response_model])
# def get_transactions(
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):
#     transactions = service.get(current_user)
#    return transactions


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=response_model)
def create_transaction(
    transaction_information: schemas.TransactionInformationCreate,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    transaction = tm.transaction(
        service.create_transaction, current_user, transaction_information
    )
    return transaction


# @router.put("/{id}", response_model=response_model)
# def update_transaction(
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):
#     transaction = tm.transaction(service.update, data)
#     json = mapper.to_json(transaction)
#     response = arh.response(data=json)
#     return response


# @router.delete("/delete/{id}", status=status.HTTP_204_NO_CONTENT)
# def delete_transaction(
#     id: int,
#     current_user: models.User = Depends(oauth2.get_current_user),
# ):
#     result = tm.transaction(service.delete, data)
#     response = arh.response(result)
#     return response
