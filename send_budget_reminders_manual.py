#!/usr/bin/env python3
"""
Ручная отправка напоминаний о бюджете
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, TournamentBudget
from services.budget_service import get_budget_service
from datetime import datetime, date, timedelta
import pytz

async def send_budget_reminders_manual():
    """Ручная отправка напоминаний о бюджете"""
    print("💰 РУЧНАЯ ОТПРАВКА НАПОМИНАНИЙ О БЮДЖЕТЕ")
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
            # Создаем сервис бюджета (нужен bot для отправки сообщений)
            print("⚠️ Для отправки напоминаний нужен бот. Создаем заглушку...")
            
            # Отправляем напоминания
            for tournament in tournaments:
                print(f"\n🏆 Турнир: {tournament.name} ({tournament.date})")
                
                # Проверим, есть ли бюджет
                budget = session.query(TournamentBudget).filter(TournamentBudget.tournament_id == tournament.tournament_id).first()
                if budget:
                    print(f"   💰 Бюджет уже установлен: {budget.total_budget} руб.")
                else:
                    print(f"   💰 Бюджет НЕ установлен - напоминание должно быть отправлено")
        else:
            print("❌ Нет турниров на завтра")
            
    finally:
        session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_budget_reminders_manual())
