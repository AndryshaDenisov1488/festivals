#!/usr/bin/env python3
"""
Создание записей об оплате для существующих турниров
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, JudgePayment, Registration, RegistrationStatus
from datetime import datetime

def create_payment_records():
    """Создает записи об оплате для всех утвержденных судей"""
    print("💰 СОЗДАНИЕ ЗАПИСЕЙ ОБ ОПЛАТЕ")
    print("=" * 50)
    
    session = SessionLocal()
    try:
        # Найдем все турниры
        tournaments = session.query(Tournament).order_by(Tournament.date).all()
        print(f"📊 Всего турниров: {len(tournaments)}")
        
        total_created = 0
        
        for tournament in tournaments:
            print(f"\n🏆 Турнир: {tournament.name} ({tournament.date})")
            
            # Получаем всех утвержденных судей
            approved_judges = session.query(Registration).filter(
                Registration.tournament_id == tournament.tournament_id,
                Registration.status == RegistrationStatus.APPROVED
            ).all()
            
            print(f"   👥 Утвержденных судей: {len(approved_judges)}")
            
            if not approved_judges:
                print("   ⚠️ Нет утвержденных судей")
                continue
            
            # Создаем записи об оплате
            created_count = 0
            for registration in approved_judges:
                # Проверяем, не создана ли уже запись
                existing_payment = session.query(JudgePayment).filter(
                    JudgePayment.user_id == registration.user_id,
                    JudgePayment.tournament_id == tournament.tournament_id
                ).first()
                
                if not existing_payment:
                    payment = JudgePayment(
                        user_id=registration.user_id,
                        tournament_id=tournament.tournament_id,
                        is_paid=False,
                        reminder_sent=False
                    )
                    session.add(payment)
                    created_count += 1
                    print(f"     ✅ Создана запись для судьи {registration.user.first_name} {registration.user.last_name}")
                else:
                    print(f"     ⚠️ Запись уже существует для судьи {registration.user.first_name} {registration.user.last_name}")
            
            session.commit()
            total_created += created_count
            print(f"   📝 Создано записей: {created_count}")
        
        print(f"\n✅ Итого создано записей об оплате: {total_created}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_payment_records()
