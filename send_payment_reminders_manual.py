#!/usr/bin/env python3
"""
Ручная отправка напоминаний об оплате
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, JudgePayment, Registration, RegistrationStatus
from services.payment_system import get_payment_system
from datetime import datetime, date, timedelta
import pytz

async def send_payment_reminders_manual():
    """Ручная отправка напоминаний об оплате"""
    print("💸 РУЧНАЯ ОТПРАВКА НАПОМИНАНИЙ ОБ ОПЛАТЕ")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Найдем турниры, которые проходят сегодня
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        today = now_msk.date()
        
        print(f"Текущее время MSK: {now_msk}")
        print(f"Сегодня: {today}")
        
        tournaments = session.query(Tournament).filter(Tournament.date == today).all()
        print(f"Турниров сегодня: {len(tournaments)}")
        
        if tournaments:
            # Создаем сервис оплаты (нужен bot для отправки сообщений)
            print("⚠️ Для отправки напоминаний нужен бот. Создаем заглушку...")
            
            # Отправляем напоминания
            for tournament in tournaments:
                print(f"\n🏆 Турнир: {tournament.name} ({tournament.date})")
                
                # Проверим записи об оплате
                payments = session.query(JudgePayment).filter(JudgePayment.tournament_id == tournament.tournament_id).all()
                unpaid = [p for p in payments if not p.is_paid]
                print(f"   💰 Записей об оплате: {len(payments)}, неоплаченных: {len(unpaid)}")
                
                if unpaid:
                    print(f"   📤 Напоминания должны быть отправлены для {len(unpaid)} судей:")
                    for payment in unpaid:
                        print(f"     - {payment.user.first_name} {payment.user.last_name} (ID: {payment.user_id})")
                else:
                    print(f"   ✅ Все оплачено")
        else:
            print("❌ Нет турниров сегодня")
            
    finally:
        session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_payment_reminders_manual())
