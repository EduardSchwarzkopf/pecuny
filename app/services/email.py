from fastapi import Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from starlette.responses import JSONResponse

from app import schemas
from app.config import settings
from app.logger import get_logger
from app.models import User
from app.schemas import EmailSchema

logger = get_logger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_FROM_NAME=settings.app_name,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER="templates",
)


async def _send(email: EmailSchema, subject: str, template_name: str) -> JSONResponse:
    """
    Sends an email.

    Args:
        email: The email object.
        subject: The subject of the email.
        template_name: The name of the email template.

    Returns:
        JSONResponse: A JSON response indicating the status of the email sending.

    Raises:
        ValueError: If the email key is missing from the email model dump.
        Exception: If the email could not be sent.
    """

    email_dump = email.model_dump()
    recipients = email_dump.get("email")

    if recipients is None:
        raise ValueError(
            f"Email key is missing from the email model dump - [email_dump]: {email_dump}",
        )

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=email_dump.get("body"),
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name=template_name)
        return JSONResponse(status_code=200, content={"message": "email has been sent"})
    except Exception as e:
        logger.error(
            "Email could not be sent due to %s",
            e,
        )
        raise


async def send_welcome(user: User, token: str) -> JSONResponse:
    """
    Sends a welcome email to a user.

    Args:
        user: The user object.
        token: The token for email verification.

    Returns:
        JSONResponse: A JSON response indicating the status of the email sending.

    Raises:
        None
    """

    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": settings.domain, "token": token},
    )
    return await _send(email, "Welcome! 🎉", template_name="emails/welcome.html")


async def send_forgot_password(user: User, token: str) -> JSONResponse:
    """
    Sends a forgot password email to a user.

    Args:
        user: The user object.
        token: The token for password reset.

    Returns:
        JSONResponse: A JSON response indicating the status of the email sending.

    Raises:
        None
    """

    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": settings.domain, "token": token},
    )

    return await _send(
        email, "Reset Password Request", template_name="emails/forgot-password.html"
    )


async def send_email_verification(
    user: User, token: str, request: Request
) -> JSONResponse:
    """
    Sends a new token email to a user.

    Args:
        user: The user object.
        token: The new token for verification.

    Returns:
        JSONResponse: A JSON response indicating the status of the email sending.

    Raises:
        None
    """

    email = EmailSchema(
        email=[user.email],
        body={
            "user": user,
            "verify_email_url": request.url_for("verify_email"),
            "new_token_url": request.url_for("get_new_token"),
            "token": token,
        },
    )
    return await _send(
        email, "Your verification Token!", template_name="emails/new-token.html"
    )


async def send_transaction_import_report(
    user: User,
    total_transactions,
    failed_transaction_list=list[schemas.TransactionInformationCreate],
):
    """
    Sends a transaction import report email to a user.

    Args:
        user: The user object.
        total_transactions: The total number of transactions.
        failed_transactions_list: The list of failed transactions.

    Returns:
        JSONResponse: A JSON response indicating the status of the email sending.

    Raises:
        None
    """
    failed_transactions_count = len(failed_transaction_list)
    email = EmailSchema(
        email=[user.email],
        body={
            "user": user,
            "failed_transaction_list": failed_transaction_list,
            "total_transactions": total_transactions,
            "successful_imports": total_transactions - failed_transactions_count,
            "failed_imports": failed_transactions_count,
        },
    )
    return await _send(
        email,
        "Your transaction import report!",
        template_name="emails/transaction-import-report.html",
    )
