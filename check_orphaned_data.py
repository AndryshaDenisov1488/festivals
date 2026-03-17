#!/usr/bin/env python3
"""
Скрипт для проверки и очистки "висячих" записей после удаления турниров
Находит регистрации, платежи и бюджеты, которые ссылаются на несуществующие турниры
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, Registration, JudgePayment, TournamentBudget
from sqlalchemy import text

def check_orphaned_data():
    """Проверяет наличие висячих записей"""
    session = SessionLocal()
    
    try:
        print("=" * 80)
        print("🔍 ПРОВЕРКА ВИСЯЧИХ ЗАПИСЕЙ ПОСЛЕ УДАЛЕНИЯ ТУРНИРОВ")
        print("=" * 80)
        print()
        
        # Получаем все ID существующих турниров
        existing_tournament_ids = set(
            session.query(Tournament.tournament_id).all()
        )
        existing_tournament_ids = {tid[0] for tid in existing_tournament_ids}
        
        print(f"✅ Найдено существующих турниров: {len(existing_tournament_ids)}")
        print()
        
        # 1. Проверяем регистрации
        all_registrations = session.query(Registration).all()
        orphaned_registrations = []
        
        for reg in all_registrations:
            if reg.tournament_id not in existing_tournament_ids:
                orphaned_registrations.append(reg)
        
        print(f"📝 РЕГИСТРАЦИИ:")
        print(f"   Всего регистраций: {len(all_registrations)}")
        print(f"   ⚠️  Висячих регистраций (турнир удален): {len(orphaned_registrations)}")
        
        if orphaned_registrations:
            print("   Проблемные регистрации:")
            for reg in orphaned_registrations[:10]:  # Показываем первые 10
                user = session.query(User).get(reg.user_id)
                user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {reg.user_id}"
                print(f"      - ID: {reg.registration_id}, User: {user_name}, Tournament ID: {reg.tournament_id}")
            if len(orphaned_registrations) > 10:
                print(f"      ... и еще {len(orphaned_registrations) - 10}")
        print()
        
        # 2. Проверяем платежи
        all_payments = session.query(JudgePayment).all()
        orphaned_payments = []
        
        for payment in all_payments:
            if payment.tournament_id not in existing_tournament_ids:
                orphaned_payments.append(payment)
        
        print(f"💰 ПЛАТЕЖИ:")
        print(f"   Всего платежей: {len(all_payments)}")
        print(f"   ⚠️  Висячих платежей (турнир удален): {len(orphaned_payments)}")
        
        if orphaned_payments:
            print("   Проблемные платежи:")
            for payment in orphaned_payments[:10]:  # Показываем первые 10
                user = session.query(User).get(payment.user_id)
                user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {payment.user_id}"
                amount = payment.amount if payment.amount else "N/A"
                print(f"      - ID: {payment.payment_id}, User: {user_name}, Tournament ID: {payment.tournament_id}, Amount: {amount}")
            if len(orphaned_payments) > 10:
                print(f"      ... и еще {len(orphaned_payments) - 10}")
        print()
        
        # 3. Проверяем бюджеты
        all_budgets = session.query(TournamentBudget).all()
        orphaned_budgets = []
        
        for budget in all_budgets:
            if budget.tournament_id not in existing_tournament_ids:
                orphaned_budgets.append(budget)
        
        print(f"💵 БЮДЖЕТЫ:")
        print(f"   Всего бюджетов: {len(all_budgets)}")
        print(f"   ⚠️  Висячих бюджетов (турнир удален): {len(orphaned_budgets)}")
        
        if orphaned_budgets:
            print("   Проблемные бюджеты:")
            for budget in orphaned_budgets:
                print(f"      - ID: {budget.budget_id}, Tournament ID: {budget.tournament_id}, Budget: {budget.total_budget}")
        print()
        
        # Итоговая статистика
        total_orphaned = len(orphaned_registrations) + len(orphaned_payments) + len(orphaned_budgets)
        
        print("=" * 80)
        print("📊 ИТОГО:")
        print(f"   ⚠️  Всего висячих записей: {total_orphaned}")
        print("=" * 80)
        print()
        
        if total_orphaned > 0:
            print("💡 Рекомендация: Запустите скрипт с флагом --fix для автоматической очистки")
            print("   Или используйте функцию удаления турнира в боте (она теперь удаляет все связанные данные)")
        else:
            print("✅ Висячих записей не найдено!")
        
        return {
            'orphaned_registrations': orphaned_registrations,
            'orphaned_payments': orphaned_payments,
            'orphaned_budgets': orphaned_budgets
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


def fix_orphaned_data(dry_run=True):
    """Удаляет висячие записи"""
    session = SessionLocal()
    
    try:
        orphaned_data = check_orphaned_data()
        
        if not orphaned_data:
            return
        
        if dry_run:
            print("\n" + "=" * 80)
            print("🔍 РЕЖИМ ПРОВЕРКИ (dry-run)")
            print("=" * 80)
            print("Для реального удаления запустите: python check_orphaned_data.py --fix")
            return
        
        print("\n" + "=" * 80)
        print("🗑️  УДАЛЕНИЕ ВИСЯЧИХ ЗАПИСЕЙ")
        print("=" * 80)
        print()
        
        deleted_count = 0
        
        # Удаляем висячие бюджеты
        if orphaned_data['orphaned_budgets']:
            budget_ids = [b.budget_id for b in orphaned_data['orphaned_budgets']]
            deleted = session.query(TournamentBudget).filter(
                TournamentBudget.budget_id.in_(budget_ids)
            ).delete(synchronize_session=False)
            deleted_count += deleted
            print(f"✅ Удалено висячих бюджетов: {deleted}")
        
        # Удаляем висячие платежи
        if orphaned_data['orphaned_payments']:
            payment_ids = [p.payment_id for p in orphaned_data['orphaned_payments']]
            deleted = session.query(JudgePayment).filter(
                JudgePayment.payment_id.in_(payment_ids)
            ).delete(synchronize_session=False)
            deleted_count += deleted
            print(f"✅ Удалено висячих платежей: {deleted}")
        
        # Удаляем висячие регистрации
        if orphaned_data['orphaned_registrations']:
            registration_ids = [r.registration_id for r in orphaned_data['orphaned_registrations']]
            deleted = session.query(Registration).filter(
                Registration.registration_id.in_(registration_ids)
            ).delete(synchronize_session=False)
            deleted_count += deleted
            print(f"✅ Удалено висячих регистраций: {deleted}")
        
        session.commit()
        
        print()
        print(f"✅ Всего удалено записей: {deleted_count}")
        print("✅ База данных очищена от висячих записей!")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    from models import User
    
    import sys
    if '--fix' in sys.argv:
        print("⚠️  ВНИМАНИЕ: Будет выполнено реальное удаление висячих записей!")
        confirm = input("Продолжить? (yes/no): ").lower().strip()
        if confirm in ['yes', 'y', 'да']:
            fix_orphaned_data(dry_run=False)
        else:
            print("❌ Операция отменена")
    else:
        check_orphaned_data()
        print("\n💡 Для удаления висячих записей запустите: python check_orphaned_data.py --fix")

