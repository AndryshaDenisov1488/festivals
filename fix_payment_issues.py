#!/usr/bin/env python3
"""
Скрипт для исправления проблем с оплатами судей в базе данных.
Исправляет:
1. Удаляет записи об оплате для неутвержденных судей (регистрации удалены)
2. Помечает некорректные суммы как требующие исправления (можно вручную исправить)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User, Registration, RegistrationStatus
from sqlalchemy import and_, or_
from datetime import datetime

# Минимальная сумма оплаты
MIN_PAYMENT_AMOUNT = 3500

def fix_payment_issues(dry_run=True):
    """
    Исправляет проблемы с оплатами
    
    Args:
        dry_run: Если True, только показывает что будет исправлено, не изменяет БД
    """
    print("=" * 80)
    if dry_run:
        print("🔍 РЕЖИМ ПРОСМОТРА (dry-run) - изменения НЕ будут применены")
    else:
        print("⚠️  РЕЖИМ ИСПРАВЛЕНИЯ - изменения БУДУТ применены к БД!")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    try:
        # 1. Удаляем записи об оплате для неутвержденных судей
        print("1️⃣ УДАЛЕНИЕ ЗАПИСЕЙ ОБ ОПЛАТЕ ДЛЯ НЕУТВЕРЖДЕННЫХ СУДЕЙ")
        print("-" * 80)
        
        all_payments = session.query(JudgePayment).join(Tournament).join(User).all()
        orphaned_payments = []
        
        for payment in all_payments:
            registration = session.query(Registration).filter(
                and_(
                    Registration.user_id == payment.user_id,
                    Registration.tournament_id == payment.tournament_id,
                    Registration.status == RegistrationStatus.APPROVED
                )
            ).first()
            
            if not registration:
                orphaned_payments.append(payment)
        
        if orphaned_payments:
            print(f"   Найдено записей для удаления: {len(orphaned_payments)}\n")
            
            deleted_count = 0
            for payment in orphaned_payments:
                any_registration = session.query(Registration).filter(
                    and_(
                        Registration.user_id == payment.user_id,
                        Registration.tournament_id == payment.tournament_id
                    )
                ).first()
                
                status_text = f"статус: {any_registration.status}" if any_registration else "регистрация удалена"
                
                print(f"   {'[УДАЛЕНО]' if not dry_run else '[БУДЕТ УДАЛЕНО]'} "
                      f"{payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                print(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                print(f"      Проблема: {status_text}")
                print(f"      Оплачено: {'Да' if payment.is_paid else 'Нет'}")
                if payment.is_paid and payment.amount:
                    print(f"      Сумма: {payment.amount} руб.")
                print()
                
                if not dry_run:
                    session.delete(payment)
                    deleted_count += 1
            
            if not dry_run:
                session.commit()
                print(f"   ✅ Удалено записей: {deleted_count}\n")
            else:
                print(f"   ℹ️  Будет удалено записей: {len(orphaned_payments)}\n")
        else:
            print("   ✅ Нет записей для удаления!\n")
        
        # 2. Некорректные суммы - помечаем для ручного исправления
        print("2️⃣ НЕКОРРЕКТНЫЕ СУММЫ ОПЛАТЫ")
        print("-" * 80)
        
        incorrect_amounts = session.query(JudgePayment).filter(
            and_(
                JudgePayment.is_paid == True,
                or_(
                    JudgePayment.amount < MIN_PAYMENT_AMOUNT,
                    JudgePayment.amount.is_(None)
                )
            )
        ).join(Tournament).join(User).order_by(Tournament.date.desc()).all()
        
        if incorrect_amounts:
            print(f"   Найдено записей с некорректными суммами: {len(incorrect_amounts)}\n")
            print("   ⚠️  ВНИМАНИЕ: Эти записи требуют РУЧНОГО исправления!")
            print("   Рекомендуется связаться с судьями и уточнить правильную сумму.\n")
            
            for payment in incorrect_amounts:
                amount_text = f"{payment.amount} руб." if payment.amount else "НЕ УКАЗАНА"
                print(f"   ⚠️ {payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                print(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                print(f"      Текущая сумма: {amount_text}")
                if payment.amount and payment.amount < MIN_PAYMENT_AMOUNT:
                    print(f"      ❌ Сумма меньше минимальной ({MIN_PAYMENT_AMOUNT} руб.)")
                elif payment.amount is None:
                    print(f"      ❌ Сумма не указана")
                print()
            
            print("   💡 Для исправления можно:")
            print("      1. Связаться с судьей и уточнить сумму")
            print("      2. Обновить запись в БД вручную через SQL:")
            print("         UPDATE judge_payments SET amount = <правильная_сумма> WHERE payment_id = <id>;")
            print()
        else:
            print("   ✅ Все суммы оплаты корректны!\n")
        
        # 3. Резюме
        print("=" * 80)
        print("📊 РЕЗЮМЕ")
        print("=" * 80)
        print(f"   Записей для удаления: {len(orphaned_payments)}")
        print(f"   Записей с некорректными суммами: {len(incorrect_amounts)}")
        print()
        
        if dry_run:
            print("   💡 Для применения изменений запустите скрипт с параметром --apply")
            print("      python fix_payment_issues.py --apply")
        else:
            print("   ✅ Изменения применены к базе данных!")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    if not dry_run:
        print("\n" + "=" * 80)
        print("⚠️  ВНИМАНИЕ! Вы запустили скрипт в режиме ИСПРАВЛЕНИЯ!")
        print("   Изменения будут применены к базе данных.")
        print("=" * 80)
        response = input("\nПродолжить? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("Отменено.")
            sys.exit(0)
        print()
    
    fix_payment_issues(dry_run=dry_run)

