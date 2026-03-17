import smtplib
from email.message import EmailMessage
from typing import Optional

from config import os


SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "")


def send_email(to: str, subject: str, text: str, html: Optional[str] = None) -> None:
    if not SMTP_HOST or not SMTP_FROM:
        # SMTP not configured, silently skip (can be logged later)
        return

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)

    if html:
        msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_login_code_email(email: str, code: str) -> None:
    subject = "Код входа на портал судей"
    text = (
        "Ваш код для входа на портал судей:\n\n"
        f"{code}\n\n"
        "Код действителен ограниченное время. Если вы не запрашивали вход, просто игнорируйте это письмо."
    )
    send_email(email, subject, text)

