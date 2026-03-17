#!/usr/bin/env python3
"""
Тест напоминаний о бюджете
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, TournamentBudget, Registration, RegistrationStatus
from services.budget_service import get_budget_service
from datetime import datetime, date, timedelta
import pytz

def test_budget_reminders():
    """Тест напоминаний о бюджете"""
    print("🧪 ТЕСТ НАПОМИНАНИЙ О БЮДЖЕТЕ")
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
            
            # Проверим бюджет
            budget = session.query(TournamentBudget).filter(TournamentBudget.tournament_id == t.tournament_id).first()
            if budget:
                print(f"   💰 Бюджет: {budget.total_budget} руб.")
            else:
                print(f"   💰 Бюджет: НЕ УСТАНОВЛЕН")
        
        # Проверим логику напоминаний
        print(f"\n⏰ Проверка логики напоминаний:")
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        target_time = now_msk + timedelta(hours=12)
        target_date = target_time.date()
        
        print(f"   Текущее время MSK: {now_msk}")
        print(f"   Время через 12 часов: {target_time}")
        print(f"   Дата через 12 часов: {target_date}")
        
        # Найдем турниры на завтра
        tomorrow_tournaments = session.query(Tournament).filter(Tournament.date == target_date).all()
        print(f"   Турниров на завтра: {len(tomorrow_tournaments)}")
        
        for t in tomorrow_tournaments:
            print(f"     - {t.name} ({t.date})")
            
            # Проверим, есть ли бюджет
            budget = session.query(TournamentBudget).filter(TournamentBudget.tournament_id == t.tournament_id).first()
            if budget:
                print(f"       Бюджет: {budget.total_budget} руб.")
            else:
                print(f"       Бюджет: НЕ УСТАНОВЛЕН (напоминание должно прийти)")
        
    finally:
        session.close()

if __name__ == "__main__":
    test_budget_reminders()
