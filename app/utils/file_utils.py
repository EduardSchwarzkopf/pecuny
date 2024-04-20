import csv
from decimal import InvalidOperation
from io import StringIO

from fastapi import BackgroundTasks, HTTPException, UploadFile
from pydantic import ValidationError

from app.background_tasks import import_transactions
from app.models import User
from app.schemas import TransactionInformationCreate


async def process_csv_file(
    account_id: int,
    file: UploadFile,
    current_user: User,
    background_tasks: BackgroundTasks,
):
    """
    Processes a CSV file upload.

    Args:
        account_id: The ID of the account.
        file: The uploaded CSV file.
        current_user: The current authenticated and verified user.
        background_tasks: Background tasks to add tasks to.
        is_api_route: Flag to indicate if the route is an API route.

    Returns:
        Response or RedirectResponse: Depending on the route, returns an HTTP response or redirects.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        contents_str = contents.decode()
        csv_file = StringIO(contents_str)
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=e.reason) from e

    reader = csv.DictReader(csv_file, delimiter=";")

    transaction_list = []
    for row in reader:
        try:
            transaction_list.append(
                TransactionInformationCreate(account_id=account_id, **row)
            )
        except ValidationError as e:
            first_error = e.errors()[0]
            custom_error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            raise HTTPException(status_code=400, detail=custom_error_message) from e
        except InvalidOperation as e:
            msg = f"Invalid value on line {reader.line_num} on value {row['amount']}"
            raise HTTPException(status_code=400, detail=msg) from e

    background_tasks.add_task(import_transactions, current_user, transaction_list)
