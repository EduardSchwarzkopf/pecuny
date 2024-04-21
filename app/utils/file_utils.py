import csv
from io import StringIO

from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.background_tasks import import_transactions_from_csv
from app.models import User


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

    background_tasks.add_task(
        import_transactions_from_csv, current_user, account_id, reader
    )
