#!/usr/bin/env python3
"""
Тест напоминаний об оплате
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, JudgePayment, Registration, RegistrationStatus
from services.payment_system import get_payment_system
from datetime import datetime, date, timedelta
import pytz

def test_payment_reminders():
    """Тест напоминаний об оплате"""
    print("🧪 ТЕСТ НАПОМИНАНИЙ ОБ ОПЛАТЕ")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Проверим турниры
        tournaments = session.query(Tournament).order_by(Tournament.date).all()
        print(f"📊 Всего турниров: {len(tournaments)}")
        
        for t in tournaments:
            print(f"\n🏆 Турнир: {t.name}")
            print(f"   📅 Дата: {t.date}")
            
            # Проверим заявки
            registrations = session.query(Registration).filter(Registration.tournament_id == t.tournament_id).all()
            approved = [r for r in registrations if r.status == RegistrationStatus.APPROVED]
            print(f"   👥 Заявок: {len(registrations)}, утверждено: {len(approved)}")
            
            # Проверим записи об оплате
            payments = session.query(JudgePayment).filter(JudgePayment.tournament_id == t.tournament_id).all()
            print(f"   💰 Записей об оплате: {len(payments)}")
            
            for payment in payments:
                print(f"     - Судья {payment.user_id}: оплачен={payment.is_paid}, напоминание={payment.reminder_sent}")
        
        # Проверим логику напоминаний об оплате
        print(f"\n⏰ Проверка логики напоминаний об оплате:")
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        today = now_msk.date()
        
        print(f"   Текущее время MSK: {now_msk}")
        print(f"   Сегодня: {today}")
        
        # Найдем турниры, которые проходят сегодня
        today_tournaments = session.query(Tournament).filter(Tournament.date == today).all()
        print(f"   Турниров сегодня: {len(today_tournaments)}")
        
        for t in today_tournaments:
            print(f"     - {t.name} ({t.date})")
            
            # Проверим записи об оплате
            payments = session.query(JudgePayment).filter(JudgePayment.tournament_id == t.tournament_id).all()
            unpaid = [p for p in payments if not p.is_paid]
            print(f"       Записей об оплате: {len(payments)}, неоплаченных: {len(unpaid)}")
            
            for payment in unpaid:
                print(f"         - Судья {payment.user_id}: напоминание={payment.reminder_sent}")
        
    finally:
        session.close()

if __name__ == "__main__":
    test_payment_reminders()
