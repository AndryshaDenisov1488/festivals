#!/usr/bin/env python3
"""
Скрипт для полной очистки данных о тестовом турнире из базы данных
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, TournamentBudget, Registration
from sqlalchemy import and_

def cleanup_test_tournament():
    """Удаляет все данные о тестовом турнире из базы данных"""
    
    session = SessionLocal()
    try:
        print("🧹 ОЧИСТКА ДАННЫХ О ТЕСТОВОМ ТУРНИРЕ")
        print("=" * 60)
        
        # Находим тестовый турнир
        test_tournament = session.query(Tournament).filter(
            Tournament.name.like("%Тестовый%")
        ).first()
        
        if not test_tournament:
            print("❌ Тестовый турнир не найден в базе данных!")
            return
        
        print(f"🏆 Найден турнир: {test_tournament.name}")
        print(f"📅 Дата: {test_tournament.date.strftime('%d.%m.%Y')}")
        print(f"🆔 ID: {test_tournament.tournament_id}")
        print()
        
        # Подсчитываем данные для удаления
        registrations_count = session.query(Registration).filter(
            Registration.tournament_id == test_tournament.tournament_id
        ).count()
        
        payments_count = session.query(JudgePayment).filter(
            JudgePayment.tournament_id == test_tournament.tournament_id
        ).count()
        
        budget_count = session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id == test_tournament.tournament_id
        ).count()
        
        print("📊 ДАННЫЕ ДЛЯ УДАЛЕНИЯ:")
        print(f"   📝 Заявки судей: {registrations_count}")
        print(f"   💰 Записи об оплате: {payments_count}")
        print(f"   💵 Бюджет турнира: {budget_count}")
        print(f"   🏆 Сам турнир: 1")
        print()
        
        # Показываем детали
        if registrations_count > 0:
            print("👥 ЗАЯВКИ СУДЕЙ:")
            registrations = session.query(Registration).join(Tournament).filter(
                Registration.tournament_id == test_tournament.tournament_id
            ).all()
            for reg in registrations:
                print(f"   • {reg.user.first_name} {reg.user.last_name} - {reg.status}")
        
        if payments_count > 0:
            print("\n💰 ЗАПИСИ ОБ ОПЛАТЕ:")
            payments = session.query(JudgePayment).join(Tournament).filter(
                JudgePayment.tournament_id == test_tournament.tournament_id
            ).all()
            for payment in payments:
                status = "Оплачен" if payment.is_paid else "Не оплачен"
                amount = f"{payment.amount} руб." if payment.amount else "Не указана"
                print(f"   • {payment.user.first_name} {payment.user.last_name} - {status} ({amount})")
        
        if budget_count > 0:
            print("\n💵 БЮДЖЕТ ТУРНИРА:")
            budget = session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == test_tournament.tournament_id
            ).first()
            if budget:
                print(f"   • Общий бюджет: {budget.total_budget} руб.")
                print(f"   • Выплачено судьям: {budget.judges_payment or 0} руб.")
                print(f"   • Прибыль админа: {budget.admin_profit or 0} руб.")
        
        print()
        print("⚠️ ВНИМАНИЕ: Это действие необратимо!")
        print("Все данные о тестовом турнире будут удалены навсегда.")
        
        # Запрашиваем подтверждение
        confirm = input("\nПродолжить удаление? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y', 'да']:
            print("❌ Операция отменена")
            return
        
        print("\n🗑️ НАЧИНАЕМ УДАЛЕНИЕ...")
        
        # Удаляем в правильном порядке (сначала зависимые таблицы)
        deleted_count = 0
        
        # 1. Удаляем записи об оплате
        if payments_count > 0:
            deleted_payments = session.query(JudgePayment).filter(
                JudgePayment.tournament_id == test_tournament.tournament_id
            ).delete()
            deleted_count += deleted_payments
            print(f"✅ Удалено записей об оплате: {deleted_payments}")
        
        # 2. Удаляем бюджет турнира
        if budget_count > 0:
            deleted_budgets = session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == test_tournament.tournament_id
            ).delete()
            deleted_count += deleted_budgets
            print(f"✅ Удалено записей бюджета: {deleted_budgets}")
        
        # 3. Удаляем заявки судей
        if registrations_count > 0:
            deleted_registrations = session.query(Registration).filter(
                Registration.tournament_id == test_tournament.tournament_id
            ).delete()
            deleted_count += deleted_registrations
            print(f"✅ Удалено заявок судей: {deleted_registrations}")
        
        # 4. Удаляем сам турнир
        tournament_name = test_tournament.name
        tournament_date = test_tournament.date.strftime('%d.%m.%Y')
        session.delete(test_tournament)
        deleted_count += 1
        print(f"✅ Удален турнир: {tournament_name} ({tournament_date})")
        
        # Сохраняем изменения
        session.commit()
        
        print()
        print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")
        print(f"📊 Всего удалено записей: {deleted_count}")
        print("✅ Все данные о тестовом турнире удалены из базы данных")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        session.rollback()
        print("🔄 Изменения отменены")
    finally:
        session.close()

def main():
    """Главная функция"""
    print("🧹 СКРИПТ ОЧИСТКИ ДАННЫХ О ТЕСТОВОМ ТУРНИРЕ")
    print("=" * 60)
    print("Этот скрипт удалит ВСЕ данные о тестовом турнире:")
    print("• Заявки судей")
    print("• Записи об оплате") 
    print("• Бюджет турнира")
    print("• Сам турнир")
    print()
    print("⚠️ ВНИМАНИЕ: Это действие необратимо!")
    print()
    
    cleanup_test_tournament()

if __name__ == "__main__":
    main()
