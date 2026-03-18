import os
import smtplib
from email.message import EmailMessage
from typing import Optional


SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "")

WEB_PORTAL_URL = os.getenv("WEB_PORTAL_URL", "https://festsfs.ru")


def _base_html(title: str, content: str, accent_color: str = "#0f172a") -> str:
    """Базовый HTML-шаблон для писем."""
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f1f5f9;color:#334155;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;">
    <tr>
      <td align="center" style="padding:24px 16px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:480px;background:#ffffff;border-radius:16px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -2px rgba(0,0,0,0.1);overflow:hidden;">
          <tr>
            <td style="background:{accent_color};padding:24px 32px;text-align:center;">
              <h1 style="margin:0;font-size:22px;font-weight:600;color:#ffffff;letter-spacing:-0.5px;">
                Кабинет судьи
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              {content}
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
              <p style="margin:0;font-size:12px;color:#64748b;">
                Веб-портал судей · <a href="{WEB_PORTAL_URL}" style="color:#0f172a;text-decoration:none;">{WEB_PORTAL_URL}</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_email(to: str, subject: str, text: str, html: Optional[str] = None) -> None:
    if not SMTP_HOST or not SMTP_FROM:
        return

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)

    if html:
        msg.add_alternative(html, subtype="html")

    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    else:
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
    content = f"""
      <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#334155;">
        Ваш код для входа на портал судей:
      </p>
      <div style="background:#f1f5f9;border-radius:12px;padding:20px;text-align:center;margin:24px 0;">
        <span style="font-size:28px;font-weight:700;letter-spacing:8px;color:#0f172a;">{code}</span>
      </div>
      <p style="margin:0;font-size:14px;line-height:1.6;color:#64748b;">
        Код действителен ограниченное время. Если вы не запрашивали вход, просто игнорируйте это письмо.
      </p>
    """
    html = _base_html("Код входа", content)
    send_email(email, subject, text, html)


def send_registration_approved_email(email: str, tournament_name: str, tournament_date: str) -> None:
    subject = f"Заявка одобрена: {tournament_name}"
    text = (
        f"Поздравляем! Ваша заявка на судейство турнира «{tournament_name}» ({tournament_date}) одобрена.\n\n"
        "Вы можете войти в кабинет судьи для просмотра деталей."
    )
    content = f"""
      <div style="text-align:center;margin-bottom:24px;">
        <span style="display:inline-block;width:56px;height:56px;background:#dcfce7;border-radius:50%;line-height:56px;font-size:28px;">✓</span>
      </div>
      <h2 style="margin:0 0 16px;font-size:20px;font-weight:600;color:#0f172a;text-align:center;">
        Заявка одобрена!
      </h2>
      <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#334155;text-align:center;">
        Ваша заявка на судейство турнира одобрена.
      </p>
      <div style="background:#f0fdf4;border-radius:12px;padding:20px;margin:24px 0;border-left:4px solid #22c55e;">
        <p style="margin:0;font-size:16px;font-weight:600;color:#166534;">{tournament_name}</p>
        <p style="margin:8px 0 0;font-size:14px;color:#15803d;">{tournament_date}</p>
      </div>
      <p style="margin:0;font-size:14px;line-height:1.6;color:#64748b;text-align:center;">
        <a href="{WEB_PORTAL_URL}" style="color:#0f172a;font-weight:600;text-decoration:none;">Войти в кабинет →</a>
      </p>
    """
    html = _base_html("Заявка одобрена", content, accent_color="#15803d")
    send_email(email, subject, text, html)


def send_registration_rejected_email(email: str, tournament_name: str, tournament_date: str) -> None:
    subject = f"Заявка отклонена: {tournament_name}"
    text = (
        f"К сожалению, ваша заявка на судейство турнира «{tournament_name}» ({tournament_date}) отклонена.\n\n"
        "Вы можете подать заявку на другие турниры в кабинете судьи."
    )
    content = f"""
      <div style="text-align:center;margin-bottom:24px;">
        <span style="display:inline-block;width:56px;height:56px;background:#fee2e2;border-radius:50%;line-height:56px;font-size:28px;color:#b91c1c;">✕</span>
      </div>
      <h2 style="margin:0 0 16px;font-size:20px;font-weight:600;color:#0f172a;text-align:center;">
        Заявка отклонена
      </h2>
      <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#334155;text-align:center;">
        К сожалению, ваша заявка на судейство турнира не была одобрена.
      </p>
      <div style="background:#fef2f2;border-radius:12px;padding:20px;margin:24px 0;border-left:4px solid #ef4444;">
        <p style="margin:0;font-size:16px;font-weight:600;color:#991b1b;">{tournament_name}</p>
        <p style="margin:8px 0 0;font-size:14px;color:#b91c1c;">{tournament_date}</p>
      </div>
      <p style="margin:0;font-size:14px;line-height:1.6;color:#64748b;text-align:center;">
        Вы можете подать заявку на другие турниры в <a href="{WEB_PORTAL_URL}" style="color:#0f172a;font-weight:600;text-decoration:none;">кабинете судьи</a>.
      </p>
    """
    html = _base_html("Заявка отклонена", content, accent_color="#b91c1c")
    send_email(email, subject, text, html)


def send_tournament_reminder_email(email: str, tournament_name: str, tournament_date: str) -> None:
    subject = f"Напоминание: турнир завтра — {tournament_name}"
    text = (
        f"Добрый день!\n\n"
        f"Напоминаем, что вы утверждены судить турнир «{tournament_name}» ({tournament_date}) завтра.\n\n"
        "Если ваши планы поменялись, напишите Андрюше."
    )
    content = f"""
      <div style="text-align:center;margin-bottom:24px;">
        <span style="display:inline-block;width:56px;height:56px;background:#dbeafe;border-radius:50%;line-height:56px;font-size:28px;">📅</span>
      </div>
      <h2 style="margin:0 0 16px;font-size:20px;font-weight:600;color:#0f172a;text-align:center;">
        Напоминание о турнире
      </h2>
      <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#334155;text-align:center;">
        Вы утверждены судить турнир завтра. Не забудьте!
      </p>
      <div style="background:#eff6ff;border-radius:12px;padding:20px;margin:24px 0;border-left:4px solid #3b82f6;">
        <p style="margin:0;font-size:16px;font-weight:600;color:#1e40af;">{tournament_name}</p>
        <p style="margin:8px 0 0;font-size:14px;color:#2563eb;">{tournament_date}</p>
      </div>
      <p style="margin:0;font-size:14px;line-height:1.6;color:#64748b;text-align:center;">
        Если ваши планы поменялись, напишите Андрюше.
      </p>
    """
    html = _base_html("Напоминание о турнире", content, accent_color="#2563eb")
    send_email(email, subject, text, html)
