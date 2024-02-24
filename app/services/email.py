from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from starlette.responses import JSONResponse

from app.config import settings
from app.logger import get_logger
from app.models import User
from app.schemas import EmailSchema

log = get_logger(__name__)

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
    email_dump = email.model_dump()
    recipients = email_dump.get("email")

    if recipients is None:
        raise ValueError(
            "Email key is missing from the email model dump - [email_dump]: %s",
            email_dump,
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
        log.info("Email has been sent to %s", email.model_dump().get("email"))
        return JSONResponse(status_code=200, content={"message": "email has been sent"})
    except Exception as e:
        log.error(
            "Email could not be sent to %s due to %s",
            email.model_dump().get("email"),
            e,
        )
        raise


async def send_welcome(user: User, token: str) -> JSONResponse:
    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": settings.domain, "token": token},
    )
    log.info("Sending welcome email to %s", user.email)
    return await _send(email, "Welcome! 🎉", template_name="emails/welcome.html")


async def send_forgot_password(user: User, token: str) -> JSONResponse:
    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": settings.domain, "token": token},
    )

    log.info("Sending forgot password email to %s", user.email)
    return await _send(
        email, "Reset Password Request", template_name="emails/forgot-password.html"
    )


async def send_new_token(user: User, token: str) -> JSONResponse:
    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": settings.domain, "token": token},
    )
    log.info("Sending new token email to %s", user.email)
    return await _send(
        email, "Your verification Token!", template_name="emails/new-token.html"
    )
