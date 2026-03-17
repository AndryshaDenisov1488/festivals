#!/usr/bin/env python3
"""
Ручной запуск напоминаний
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, JudgePayment, Registration, RegistrationStatus
from services.budget_service import get_budget_service
from services.payment_system import get_payment_system
from datetime import datetime, date, timedelta
import pytz

def manual_budget_reminders():
    """Ручной запуск напоминаний о бюджете"""
    print("💰 РУЧНОЙ ЗАПУСК НАПОМИНАНИЙ О БЮДЖЕТЕ")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Найдем турниры на завтра
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        target_time = now_msk + timedelta(hours=12)
        target_date = target_time.date()
        
        print(f"Текущее время MSK: {now_msk}")
        print(f"Время через 12 часов: {target_time}")
        print(f"Дата через 12 часов: {target_date}")
        
        tournaments = session.query(Tournament).filter(Tournament.date == target_date).all()
        print(f"Турниров на завтра: {len(tournaments)}")
        
        if tournaments:
            # Создаем сервис бюджета
            budget_service = get_budget_service()
            
            # Отправляем напоминания
            for tournament in tournaments:
                print(f"\n🏆 Турнир: {tournament.name} ({tournament.date})")
                
                # Проверим, есть ли бюджет
                from models import TournamentBudget
                budget = session.query(TournamentBudget).filter(TournamentBudget.tournament_id == tournament.tournament_id).first()
                if budget:
                    print(f"   💰 Бюджет уже установлен: {budget.total_budget} руб.")
                else:
                    print(f"   💰 Бюджет НЕ установлен - отправляем напоминание")
                    await budget_service._send_budget_reminder(tournament)
        else:
            print("❌ Нет турниров на завтра")
            
    finally:
        session.close()

def manual_payment_reminders():
    """Ручной запуск напоминаний об оплате"""
    print("💸 РУЧНОЙ ЗАПУСК НАПОМИНАНИЙ ОБ ОПЛАТЕ")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Найдем турниры, которые закончились 1+ дней назад
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        one_day_ago = now_msk.date() - timedelta(days=1)
        
        print(f"Текущее время MSK: {now_msk}")
        print(f"Дата 1 день назад: {one_day_ago}")
        
        tournaments = session.query(Tournament).filter(Tournament.date <= one_day_ago).all()
        print(f"Турниров 1+ дней назад: {len(tournaments)}")
        
        if tournaments:
            # Создаем сервис оплаты
            payment_system = get_payment_system()
            
            # Отправляем напоминания
            for tournament in tournaments:
                print(f"\n🏆 Турнир: {tournament.name} ({tournament.date})")
                
                # Проверим записи об оплате
                payments = session.query(JudgePayment).filter(JudgePayment.tournament_id == tournament.tournament_id).all()
                unpaid = [p for p in payments if not p.is_paid]
                print(f"   💰 Записей об оплате: {len(payments)}, неоплаченных: {len(unpaid)}")
                
                if unpaid:
                    print(f"   📤 Отправляем напоминания...")
                    await payment_system.send_payment_reminders()
                else:
                    print(f"   ✅ Все оплачено")
        else:
            print("❌ Нет турниров 1+ дней назад")
            
    finally:
        session.close()

async def main():
    """Главная функция"""
    print("🚀 РУЧНОЙ ЗАПУСК НАПОМИНАНИЙ")
    print("=" * 50)
    
    choice = input("Выберите тип напоминаний (1 - бюджет, 2 - оплата, 3 - оба): ").strip()
    
    if choice == "1":
        await manual_budget_reminders()
    elif choice == "2":
        await manual_payment_reminders()
    elif choice == "3":
        await manual_budget_reminders()
        print("\n" + "="*50)
        await manual_payment_reminders()
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
