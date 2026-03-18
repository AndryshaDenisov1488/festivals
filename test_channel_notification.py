"""
Скрипт для проверки отправки уведомлений в Telegram-канал.
Запуск: python test_channel_notification.py

Проверяет BOT_TOKEN, CHANNEL_ID и отправляет тестовое сообщение.
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def test_channel_notification() -> None:
    from config import BOT_TOKEN, CHANNEL_ID

    print("\n=== Проверка уведомлений в канал ===\n")

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не задан в .env")
        return
    print("✓ BOT_TOKEN задан")

    if not CHANNEL_ID:
        print("❌ CHANNEL_ID не задан в .env")
        return
    print(f"✓ CHANNEL_ID задан: {CHANNEL_ID}")

    try:
        from aiogram import Bot

        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            CHANNEL_ID,
            "🧪 <b>Тест уведомлений</b>\n"
            "Проверка: бот может отправлять сообщения в канал.",
            parse_mode="HTML",
        )
        print("\n✅ Тестовое сообщение отправлено в канал. Проверьте канал.")
    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}")
        logger.exception("Детали ошибки")


if __name__ == "__main__":
    asyncio.run(test_channel_notification())
