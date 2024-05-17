from fastapi import HTTPException, UploadFile

from app.models import User
from app.tasks import import_transactions_from_csv


async def process_csv_file(
    account_id: int,
    file: UploadFile,
    current_user: User,
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

    import_transactions_from_csv.delay(current_user.id, account_id, contents)
