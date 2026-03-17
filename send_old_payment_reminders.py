#!/usr/bin/env python3
"""
Ручная отправка напоминаний об оплате для старых турниров
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, JudgePayment, Registration, RegistrationStatus
from services.payment_system import get_payment_system
from datetime import datetime, date, timedelta
import pytz

async def send_old_payment_reminders():
    """Отправляет напоминания об оплате для турнира 18 сентября"""
    print("💸 ОТПРАВКА НАПОМИНАНИЙ ОБ ОПЛАТЕ ДЛЯ ТУРНИРА 18 СЕНТЯБРЯ")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Найдем турнир 18 сентября
        tournament_18 = session.query(Tournament).filter(Tournament.date == date(2025, 9, 18)).first()
        if not tournament_18:
            print("❌ Турнир 18 сентября не найден")
            return
        
        print(f"🏆 Турнир: {tournament_18.name} ({tournament_18.date})")
        
        # Проверим записи об оплате
        payments = session.query(JudgePayment).filter(JudgePayment.tournament_id == tournament_18.tournament_id).all()
        unpaid = [p for p in payments if not p.is_paid]
        print(f"   💰 Записей об оплате: {len(payments)}, неоплаченных: {len(unpaid)}")
        
        if not unpaid:
            print("   ✅ Все оплачено")
            return
        
        print(f"   📤 Отправляем напоминания для {len(unpaid)} судей:")
        for payment in unpaid:
            print(f"     - {payment.user.first_name} {payment.user.last_name} (ID: {payment.user_id})")
        
        # Создаем сервис оплаты
        payment_system = get_payment_system()
        if not payment_system:
            print("❌ Не удалось создать сервис оплаты (нужен бот)")
            return
        
        # Отправляем напоминания
        print(f"\n🚀 Отправляем напоминания...")
        reminders_sent = await payment_system.send_payment_reminders()
        print(f"✅ Отправлено напоминаний: {reminders_sent}")
        
    finally:
        session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_old_payment_reminders())
