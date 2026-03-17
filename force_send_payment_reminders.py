#!/usr/bin/env python3
"""
Скрипт для принудительной отправки напоминаний об оплате
всем неоплаченным судьям тестового турнира
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone
import pytz

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User
from sqlalchemy import and_

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def send_reminder_to_judge(bot, payment: JudgePayment):
    """Отправляет напоминание конкретному судье"""
    from keyboards import payment_reminder_keyboard
    
    # Определяем тип напоминания
    if not payment.reminder_sent:
        # Первое напоминание - вежливое
        message = (
            f"💰 <b>Напоминание об оплате</b>\n\n"
            f"Привет, {payment.user.first_name}!\n\n"
            f"Прошёл день с турнира <b>«{payment.tournament.name}»</b> "
            f"({payment.tournament.date.strftime('%d.%m.%Y')}).\n\n"
            f"Андрюша заплатил вам за этот турнир? 🤔"
        )
    else:
        # Повторное напоминание - более настойчивое
        days_since_tournament = (datetime.now().date() - payment.tournament.date).days
        message = (
            f"⚠️ <b>ПОВТОРНОЕ НАПОМИНАНИЕ ОБ ОПЛАТЕ</b>\n\n"
            f"Привет, {payment.user.first_name}!\n\n"
            f"Прошло уже <b>{days_since_tournament} дней</b> с турнира <b>«{payment.tournament.name}»</b> "
            f"({payment.tournament.date.strftime('%d.%m.%Y')}).\n\n"
            f"Андрюша заплатил вам за этот турнир? 🤔\n\n"
            f"<i>Пожалуйста, ответьте, чтобы мы могли отследить оплату!</i>"
        )
    
    try:
        await bot.send_message(
            chat_id=payment.user.user_id,
            text=message,
            reply_markup=payment_reminder_keyboard(payment.payment_id),
            parse_mode='HTML'
        )
        logger.info(f"✅ Отправлено напоминание судье {payment.user.first_name} {payment.user.last_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке судье {payment.user.first_name} {payment.user.last_name}: {e}")
        return False

async def force_send_reminders():
    """Принудительно отправляет напоминания всем неоплаченным судьям тестового турнира"""
    
    # Инициализируем бота
    from config import BOT_TOKEN
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    
    session = SessionLocal()
    try:
        print("🚀 ПРИНУДИТЕЛЬНАЯ ОТПРАВКА НАПОМИНАНИЙ")
        print("=" * 60)
        
        # Находим тестовый турнир
        test_tournament = session.query(Tournament).filter(
            Tournament.name.like("%Тестовый%")
        ).first()
        
        if not test_tournament:
            print("❌ Тестовый турнир не найден!")
            return
        
        print(f"🏆 Найден турнир: {test_tournament.name}")
        print(f"📅 Дата: {test_tournament.date.strftime('%d.%m.%Y')}")
        print()
        
        # Находим всех неоплаченных судей этого турнира
        unpaid_payments = session.query(JudgePayment).join(User).filter(
            and_(
                JudgePayment.tournament_id == test_tournament.tournament_id,
                JudgePayment.is_paid == False
            )
        ).all()
        
        if not unpaid_payments:
            print("✅ Все судьи тестового турнира уже оплачены!")
            return
        
        print(f"👥 Найдено неоплаченных судей: {len(unpaid_payments)}")
        print()
        
        # Отправляем напоминания
        sent_count = 0
        failed_count = 0
        
        for payment in unpaid_payments:
            print(f"📤 Отправляем напоминание судье: {payment.user.first_name} {payment.user.last_name}")
            
            success = await send_reminder_to_judge(bot, payment)
            
            if success:
                # Обновляем статус напоминания
                payment.reminder_sent = True
                payment.reminder_date = datetime.now(timezone.utc)
                sent_count += 1
            else:
                failed_count += 1
            
            # Небольшая пауза между отправками
            await asyncio.sleep(1)
        
        # Сохраняем изменения
        session.commit()
        
        print()
        print("📊 РЕЗУЛЬТАТЫ:")
        print(f"   ✅ Успешно отправлено: {sent_count}")
        print(f"   ❌ Ошибок отправки: {failed_count}")
        print(f"   👥 Всего судей: {len(unpaid_payments)}")
        
        if sent_count > 0:
            print()
            print("🎉 Напоминания успешно отправлены!")
            print("💡 Судьи получат сообщения с кнопками 'Да, заплатил' и 'Нет, не заплатил'")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        session.rollback()
    finally:
        session.close()
        await bot.close()

def main():
    """Главная функция"""
    print("🔧 СКРИПТ ПРИНУДИТЕЛЬНОЙ ОТПРАВКИ НАПОМИНАНИЙ")
    print("=" * 60)
    print("Этот скрипт отправит напоминания об оплате всем")
    print("неоплаченным судьям тестового турнира.")
    print()
    
    # Запускаем асинхронную функцию
    asyncio.run(force_send_reminders())

if __name__ == "__main__":
    main()