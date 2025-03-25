from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
import logfire
from jinja2 import Environment, FileSystemLoader

from src.settings import settings

# Path: src/emails/service/templates/verification_email.html
TEMPLATE_DIR = Path(__file__).parent / "templates"
ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


async def send_email(recipient: str, subject: str, body: str) -> None:
    """Send an email asynchronously using aiosmtplib."""
    message = EmailMessage()
    message["From"] = settings.email_service.EMAIL_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.email_service.SMTP_HOST,
            port=settings.email_service.SMTP_PORT,
            username=settings.email_service.SMTP_USERNAME,
            password=settings.email_service.SMTP_PASSWORD,
            start_tls=settings.email_service.SMTP_STARTTLS,
        )
    except Exception as e:
        logfire.error(f"Failed to send email to {recipient}", error=e)


def render_verification_email(user_email: str, verification_link: str) -> str:
    """Render template with jinja2 tool, html templates are located in /templates dir."""
    template = ENV.get_template("verification_template.html")
    return template.render(user_email=user_email, verification_link=verification_link)
