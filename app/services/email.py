from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.schemas import EmailSchema
from starlette.responses import JSONResponse
from app.config import settings
from app.models import User

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER="templates",
)


async def _send(email: EmailSchema, subject: str, template_name: str) -> JSONResponse:
    message = MessageSchema(
        subject=subject,
        recipients=email.dict().get("email"),
        template_body=email.dict().get("body"),
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})


async def send_register(user: User) -> JSONResponse:
    email = EmailSchema(email=[user.email], body={"user": user})
    return await _send(email, "Welcome", template_name="emails/register.html")


async def send_verification(user: User, token: str) -> JSONResponse:
    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": "http://127.0.0.1:8000", "token": token},
    )
    return await _send(
        email, "Please verify your email", template_name="emails/verify-email.html"
    )


async def send_forgot_password(user: User, token: str) -> JSONResponse:
    email = EmailSchema(
        email=[user.email],
        body={"user": user, "url": "http://127.0.0.1:8000", "token": token},
    )

    return await _send(
        email, "Reset Password Request", template_name="emails/forgot-password.html"
    )
