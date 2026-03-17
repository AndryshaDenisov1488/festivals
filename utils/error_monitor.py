# utils/error_monitor.py
import logging
import traceback
from datetime import datetime, timezone
from aiogram import Bot
from config import CHANNEL_ID, ENABLE_ERROR_MONITORING
import pytz

logger = logging.getLogger(__name__)

class ErrorMonitor:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.enabled = ENABLE_ERROR_MONITORING and CHANNEL_ID
    
    async def log_critical_error(self, error: Exception, context: str = "", user_id: int = None):
        """
        Отправляет критическую ошибку в канал мониторинга
        """
        if not self.enabled:
            return
            
        try:
            # Используем MSK timezone
            msk_tz = pytz.timezone('Europe/Moscow')
            error_time = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M:%S")
            error_type = type(error).__name__
            error_message = str(error)
            
            # Формируем сообщение об ошибке
            message = f"🚨 <b>КРИТИЧЕСКАЯ ОШИБКА</b>\n\n"
            message += f"⏰ Время: {error_time}\n"
            message += f"🔍 Тип: {error_type}\n"
            message += f"📝 Сообщение: {error_message}\n"
            
            if context:
                message += f"📍 Контекст: {context}\n"
            
            if user_id:
                message += f"👤 Пользователь: {user_id}\n"
            
            # Добавляем traceback (обрезаем до 1000 символов)
            tb = traceback.format_exc()
            if len(tb) > 1000:
                tb = tb[:1000] + "..."
            message += f"\n📋 Traceback:\n<code>{tb}</code>"
            
            # Проверяем длину сообщения (лимит Telegram 4096 символов)
            if len(message) > 4000:
                message = message[:4000] + "..."
            
            await self.bot.send_message(
                CHANNEL_ID,
                message,
                parse_mode="HTML"
            )
            
            logger.critical(f"Critical error sent to monitoring channel: {error_type} - {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to send error to monitoring channel: {e}")
    
    async def log_warning(self, message: str, context: str = "", user_id: int = None):
        """
        Отправляет предупреждение в канал мониторинга
        """
        if not self.enabled:
            return
            
        try:
            # Используем MSK timezone
            msk_tz = pytz.timezone('Europe/Moscow')
            warning_time = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M:%S")
            
            warning_message = f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
            warning_message += f"⏰ Время: {warning_time}\n"
            warning_message += f"📝 Сообщение: {message}\n"
            
            if context:
                warning_message += f"📍 Контекст: {context}\n"
            
            if user_id:
                warning_message += f"👤 Пользователь: {user_id}\n"
            
            # Проверяем длину сообщения (лимит Telegram 4096 символов)
            if len(warning_message) > 4000:
                warning_message = warning_message[:4000] + "..."
            
            await self.bot.send_message(
                CHANNEL_ID,
                warning_message,
                parse_mode="HTML"
            )
            
            logger.warning(f"Warning sent to monitoring channel: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send warning to monitoring channel: {e}")

# Глобальный экземпляр (будет инициализирован в main.py)
error_monitor = None

def init_error_monitor(bot: Bot):
    """Инициализация мониторинга ошибок"""
    global error_monitor
    error_monitor = ErrorMonitor(bot)
    return error_monitor

def get_error_monitor() -> ErrorMonitor:
    """Получение экземпляра мониторинга ошибок"""
    return error_monitor
