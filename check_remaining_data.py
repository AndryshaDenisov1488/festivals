#!/usr/bin/env python3
"""
Скрипт для проверки оставшихся данных в базе после очистки тестового турнира
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, TournamentBudget, Registration, User
from sqlalchemy import func

def check_remaining_data():
    """Проверяет, какие данные останутся в базе после очистки тестового турнира"""
    
    session = SessionLocal()
    try:
        print("🔍 ПРОВЕРКА ОСТАВШИХСЯ ДАННЫХ В БАЗЕ")
        print("=" * 60)
        
        # Общая статистика
        total_users = session.query(User).count()
        total_tournaments = session.query(Tournament).count()
        total_registrations = session.query(Registration).count()
        total_payments = session.query(JudgePayment).count()
        total_budgets = session.query(TournamentBudget).count()
        
        print("📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   👥 Пользователей (судьи): {total_users}")
        print(f"   🏆 Турниров: {total_tournaments}")
        print(f"   📝 Заявок: {total_registrations}")
        print(f"   💰 Записей об оплате: {total_payments}")
        print(f"   💵 Бюджетов: {total_budgets}")
        print()
        
        # Проверяем тестовый турнир
        test_tournament = session.query(Tournament).filter(
            Tournament.name.like("%Тестовый%")
        ).first()
        
        if test_tournament:
            print("🏆 ТЕСТОВЫЙ ТУРНИР НАЙДЕН:")
            print(f"   Название: {test_tournament.name}")
            print(f"   Дата: {test_tournament.date.strftime('%d.%m.%Y')}")
            print(f"   ID: {test_tournament.tournament_id}")
            print()
            
            # Данные тестового турнира
            test_registrations = session.query(Registration).filter(
                Registration.tournament_id == test_tournament.tournament_id
            ).count()
            
            test_payments = session.query(JudgePayment).filter(
                JudgePayment.tournament_id == test_tournament.tournament_id
            ).count()
            
            test_budget = session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == test_tournament.tournament_id
            ).count()
            
            print("📊 ДАННЫЕ ТЕСТОВОГО ТУРНИРА:")
            print(f"   📝 Заявки: {test_registrations}")
            print(f"   💰 Записи об оплате: {test_payments}")
            print(f"   💵 Бюджет: {test_budget}")
            print()
            
            print("🗑️ ПОСЛЕ УДАЛЕНИЯ ТЕСТОВОГО ТУРНИРА ОСТАНЕТСЯ:")
            print(f"   👥 Пользователей: {total_users}")
            print(f"   🏆 Турниров: {total_tournaments - 1}")
            print(f"   📝 Заявок: {total_registrations - test_registrations}")
            print(f"   💰 Записей об оплате: {total_payments - test_payments}")
            print(f"   💵 Бюджетов: {total_budgets - test_budget}")
        else:
            print("✅ ТЕСТОВЫЙ ТУРНИР НЕ НАЙДЕН")
            print("База данных уже очищена от тестовых данных")
            print()
        
        # Показываем оставшиеся турниры
        remaining_tournaments = session.query(Tournament).filter(
            ~Tournament.name.like("%Тестовый%")
        ).order_by(Tournament.date).all()
        
        if remaining_tournaments:
            print("🏆 ОСТАВШИЕСЯ ТУРНИРЫ:")
            for tournament in remaining_tournaments:
                registrations_count = session.query(Registration).filter(
                    Registration.tournament_id == tournament.tournament_id
                ).count()
                
                payments_count = session.query(JudgePayment).filter(
                    JudgePayment.tournament_id == tournament.tournament_id
                ).count()
                
                print(f"   • {tournament.name} ({tournament.date.strftime('%d.%m.%Y')})")
                print(f"     📝 Заявок: {registrations_count}")
                print(f"     💰 Записей об оплате: {payments_count}")
        else:
            print("❌ НЕТ ОСТАВШИХСЯ ТУРНИРОВ")
        
        print()
        print("💡 РЕКОМЕНДАЦИИ:")
        if test_tournament:
            print("   1. Запустите: python cleanup_test_tournament.py")
            print("   2. Подтвердите удаление")
            print("   3. Проверьте результат")
        else:
            print("   ✅ База данных уже очищена")
            print("   ✅ Можно продолжать работу")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

def main():
    """Главная функция"""
    print("🔍 ПРОВЕРКА ДАННЫХ ПЕРЕД ОЧИСТКОЙ")
    print("=" * 60)
    print("Этот скрипт покажет, какие данные останутся")
    print("в базе после удаления тестового турнира.")
    print()
    
    check_remaining_data()

if __name__ == "__main__":
    main()
