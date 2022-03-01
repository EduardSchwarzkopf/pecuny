from datetime import date
from typing import List
from fastapi import Depends, APIRouter, status
from fastapi.exceptions import HTTPException
from .. import models, schemas, oauth2, transaction_manager as tm
from ..services import transactions as service

router = APIRouter(prefix="/transactions", tags=["Transactions"])
response_model = schemas.Transaction


@router.get("/", response_model=List[response_model])
def get_transactions(
    transaction_query: schemas.TransactionQuery,
    current_user: models.User = Depends(oauth2.get_current_user),
):
    transactions = service.get_transaction_list(current_user, transaction_query)
    return transactions


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


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    transaction_id: int, current_user: models.User = Depends(oauth2.get_current_user)
):
    result = tm.transaction(service.delete_transaction, current_user, transaction_id)
    if result:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content="Transaction deleted successfully",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
