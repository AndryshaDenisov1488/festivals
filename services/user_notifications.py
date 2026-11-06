"""Notifications about completed registrations; Telegram failures are non-fatal."""
import asyncio
import logging
from html import escape

logger = logging.getLogger(__name__)


async def notify_new_user(bot, channel_id, user, username=None):
    if not channel_id:
        return
    text = (
        "🆕 <b>В боте зарегистрирован новый пользователь</b>\n\n"
        f"👤 <a href=\"tg://user?id={int(user.user_id)}\">"
        f"{escape(user.first_name)} {escape(user.last_name)}</a>\n"
        f"🔧 Функция: {escape(user.function[:300])}\n"
        f"🏅 Категория: {escape(user.category[:300])}\n"
        f"🆔 ID: <code>{int(user.user_id)}</code>"
    )
    if username:
        text += f"\nTelegram: @{escape(username[:32])}"
    try:
        await asyncio.wait_for(
            bot.send_message(channel_id, text, parse_mode="HTML"), timeout=10,
        )
    except Exception as exc:
        logger.warning("New-user notification failed (user_id=%s, error=%s)", user.user_id, type(exc).__name__)
