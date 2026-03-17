#!/usr/bin/env python3
"""
Тест мониторинга ошибок
Запустите этот скрипт для проверки работы системы мониторинга
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, CHANNEL_ID
from utils.error_monitor import ErrorMonitor
from aiogram import Bot

async def test_error_monitoring():
    """Тестирует систему мониторинга ошибок"""
    print("🧪 Тестирование системы мониторинга ошибок...")
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в .env файле")
        return
    
    if not CHANNEL_ID:
        print("❌ CHANNEL_ID не найден в .env файле")
        return
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    
    # Инициализируем мониторинг
    error_monitor = ErrorMonitor(bot)
    
    try:
        # Тест 1: Критическая ошибка
        print("📤 Отправка тестовой критической ошибки...")
        test_error = Exception("Тестовая критическая ошибка для проверки мониторинга")
        await error_monitor.log_critical_error(
            test_error, 
            "test_error_monitoring", 
            user_id=123456789
        )
        print("✅ Критическая ошибка отправлена")
        
        # Небольшая пауза
        await asyncio.sleep(2)
        
        # Тест 2: Предупреждение
        print("📤 Отправка тестового предупреждения...")
        await error_monitor.log_warning(
            "Тестовое предупреждение для проверки мониторинга",
            "test_warning",
            user_id=123456789
        )
        print("✅ Предупреждение отправлено")
        
        print("🎉 Тест завершен! Проверьте канал на наличие сообщений.")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_error_monitoring())
