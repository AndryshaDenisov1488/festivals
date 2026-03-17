#!/usr/bin/env python3
"""
Скрипт для исправления всех найденных проблем в базе данных:
1. Удаляет записи об оплате для неутвержденных/удаленных регистраций
2. Исправляет некорректные суммы оплаты
3. Помечает неоплаченные записи как оплаченные с правильными суммами
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, User, Tournament, Registration, RegistrationStatus
from sqlalchemy import and_, text
from datetime import datetime

# Константы
STANDARD_PAYMENT_AMOUNT = 5000
SPECIAL_JUDGE_ID = 946719504  # Лизочка Маркова
SPECIAL_JUDGE_AMOUNT = 7000
MIN_PAYMENT_AMOUNT = 3500

def fix_invalid_registration_payments(dry_run=True):
    """Удаляет записи об оплате для неутвержденных/удаленных регистраций"""
    print("=" * 80)
    print("1️⃣  ИСПРАВЛЕНИЕ ЗАПИСЕЙ ДЛЯ НЕУТВЕРЖДЕННЫХ РЕГИСТРАЦИЙ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    deleted_count = 0
    
    try:
        all_payments = session.query(JudgePayment).all()
        
        payments_to_delete = []
        
        for payment in all_payments:
            registration = session.query(Registration).filter(
                and_(
                    Registration.user_id == payment.user_id,
                    Registration.tournament_id == payment.tournament_id
                )
            ).first()
            
            if not registration:
                payments_to_delete.append((payment, "регистрация удалена"))
            elif registration.status != RegistrationStatus.APPROVED:
                payments_to_delete.append((payment, f"статус: {registration.status}"))
        
        if not payments_to_delete:
            print("✅ Нет записей для удаления")
            return 0
        
        print(f"📋 Найдено записей для удаления: {len(payments_to_delete)}")
        print()
        
        # Показываем примеры
        print("Примеры записей для удаления:")
        for payment, reason in payments_to_delete[:5]:
            user = session.query(User).filter(User.user_id == payment.user_id).first()
            tournament = session.query(Tournament).filter(Tournament.tournament_id == payment.tournament_id).first()
            if user and tournament:
                print(f"   - {user.first_name} {user.last_name} - {tournament.name} ({tournament.date.strftime('%d.%m.%Y')}) - {reason}")
        if len(payments_to_delete) > 5:
            print(f"   ... и еще {len(payments_to_delete) - 5} записей")
        print()
        
        if dry_run:
            print("⚠️  РЕЖИМ ПРОВЕРКИ (dry-run)")
            print("   Записи НЕ будут удалены.")
            print("   Для применения изменений запустите с флагом --apply")
            return len(payments_to_delete)
        
        # Удаляем записи
        for payment, reason in payments_to_delete:
            session.delete(payment)
            deleted_count += 1
        
        session.commit()
        print(f"✅ Удалено записей: {deleted_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    
    return deleted_count

def fix_incorrect_amounts(dry_run=True):
    """Исправляет некорректные суммы оплаты"""
    print("=" * 80)
    print("2️⃣  ИСПРАВЛЕНИЕ НЕКОРРЕКТНЫХ СУММ ОПЛАТЫ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    fixed_count = 0
    
    try:
        paid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == True
        ).all()
        
        payments_to_fix = []
        
        for payment in paid_payments:
            if payment.user_id == SPECIAL_JUDGE_ID:
                # Для Лизочки Марковой - проверяем, что сумма правильная (7000)
                if payment.amount != SPECIAL_JUDGE_AMOUNT:
                    payments_to_fix.append((payment, SPECIAL_JUDGE_AMOUNT, f"Лизочка Маркова - должна быть {SPECIAL_JUDGE_AMOUNT}"))
            else:
                # Для остальных - проверяем стандартную сумму (5000)
                if payment.amount is None:
                    payments_to_fix.append((payment, STANDARD_PAYMENT_AMOUNT, "сумма не указана"))
                elif payment.amount < MIN_PAYMENT_AMOUNT:
                    payments_to_fix.append((payment, STANDARD_PAYMENT_AMOUNT, f"сумма слишком мала ({payment.amount})"))
                elif payment.amount != STANDARD_PAYMENT_AMOUNT:
                    payments_to_fix.append((payment, STANDARD_PAYMENT_AMOUNT, f"нестандартная сумма ({payment.amount})"))
        
        if not payments_to_fix:
            print("✅ Нет записей для исправления")
            return 0
        
        print(f"📋 Найдено записей для исправления: {len(payments_to_fix)}")
        print()
        
        # Показываем примеры
        print("Примеры записей для исправления:")
        for payment, new_amount, reason in payments_to_fix[:5]:
            user = session.query(User).filter(User.user_id == payment.user_id).first()
            tournament = session.query(Tournament).filter(Tournament.tournament_id == payment.tournament_id).first()
            if user and tournament:
                old_amount = payment.amount if payment.amount else "не указана"
                print(f"   - {user.first_name} {user.last_name} - {tournament.name} ({tournament.date.strftime('%d.%m.%Y')})")
                print(f"     Старая сумма: {old_amount} руб. → Новая сумма: {new_amount} руб. ({reason})")
        if len(payments_to_fix) > 5:
            print(f"   ... и еще {len(payments_to_fix) - 5} записей")
        print()
        
        if dry_run:
            print("⚠️  РЕЖИМ ПРОВЕРКИ (dry-run)")
            print("   Суммы НЕ будут изменены.")
            print("   Для применения изменений запустите с флагом --apply")
            return len(payments_to_fix)
        
        # Исправляем суммы
        for payment, new_amount, reason in payments_to_fix:
            payment.amount = new_amount
            fixed_count += 1
        
        session.commit()
        print(f"✅ Исправлено записей: {fixed_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    
    return fixed_count

def fix_unpaid_payments(dry_run=True):
    """Помечает неоплаченные записи как оплаченные с правильными суммами"""
    print("=" * 80)
    print("3️⃣  ОБНОВЛЕНИЕ НЕОПЛАЧЕННЫХ ЗАПИСЕЙ")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    updated_count = 0
    
    try:
        unpaid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == False
        ).join(User).join(Tournament).all()
        
        if not unpaid_payments:
            print("✅ Нет неоплаченных записей")
            return 0
        
        print(f"📋 Найдено неоплаченных записей: {len(unpaid_payments)}")
        print()
        
        # Группируем по судьям для статистики
        judges_stats = {}
        updates = []
        
        for payment in unpaid_payments:
            user_id = payment.user_id
            is_special = user_id == SPECIAL_JUDGE_ID
            amount = SPECIAL_JUDGE_AMOUNT if is_special else STANDARD_PAYMENT_AMOUNT
            
            if user_id not in judges_stats:
                judges_stats[user_id] = {
                    'user': payment.user,
                    'count': 0,
                    'total_amount': 0,
                    'is_special': is_special
                }
            judges_stats[user_id]['count'] += 1
            judges_stats[user_id]['total_amount'] += amount
            
            updates.append({
                'payment': payment,
                'amount': amount,
                'is_special': is_special
            })
        
        # Выводим статистику
        print("📊 Статистика по судьям:")
        for user_id, stats in sorted(judges_stats.items(), key=lambda x: (x[1]['user'].last_name, x[1]['user'].first_name)):
            user = stats['user']
            special_mark = " [ИНДИВИДУАЛЬНАЯ СУММА]" if stats['is_special'] else ""
            print(f"   {user.first_name} {user.last_name}{special_mark}: {stats['count']} записей, {stats['total_amount']} руб.")
        print()
        
        total_amount = sum(u['amount'] for u in updates)
        print(f"💰 Общая сумма для обновления: {total_amount} руб.")
        print()
        
        if dry_run:
            print("⚠️  РЕЖИМ ПРОВЕРКИ (dry-run)")
            print("   Записи НЕ будут обновлены.")
            print("   Для применения изменений запустите с флагом --apply")
            return len(updates)
        
        # Подтверждение
        print("⚠️  ВНИМАНИЕ!")
        print(f"   Будет обновлено {len(updates)} записей.")
        print(f"   Общая сумма: {total_amount} руб.")
        print()
        response = input("Продолжить? (yes/no): ")
        
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("❌ Отменено.")
            return 0
        
        # Обновляем записи
        for update in updates:
            payment = update['payment']
            amount = update['amount']
            
            payment.is_paid = True
            payment.amount = amount
            payment.payment_date = datetime.now()
            
            updated_count += 1
        
        session.commit()
        print(f"✅ Обновлено записей: {updated_count}")
        print(f"💰 Общая сумма: {total_amount} руб.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    
    return updated_count

def main():
    """Основная функция"""
    print("=" * 80)
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    print("📋 Параметры:")
    print(f"   Стандартная сумма: {STANDARD_PAYMENT_AMOUNT} руб.")
    print(f"   Лизочка Маркова (ID: {SPECIAL_JUDGE_ID}): {SPECIAL_JUDGE_AMOUNT} руб.")
    print()
    
    # Проверяем аргументы командной строки
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        dry_run = False
    
    if dry_run:
        print("⚠️  Запущен в режиме проверки (dry-run)")
        print("   Для применения изменений используйте: python fix_all_database_issues.py --apply")
        print()
    
    total_fixed = 0
    
    # 1. Удаляем записи для неутвержденных регистраций
    deleted = fix_invalid_registration_payments(dry_run)
    total_fixed += deleted
    print()
    
    # 2. Исправляем некорректные суммы
    fixed = fix_incorrect_amounts(dry_run)
    total_fixed += fixed
    print()
    
    # 3. Обновляем неоплаченные записи
    updated = fix_unpaid_payments(dry_run)
    total_fixed += updated
    print()
    
    print("=" * 80)
    if dry_run:
        print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
        print(f"   Найдено проблем для исправления: {total_fixed}")
        print("   Для применения изменений используйте: python fix_all_database_issues.py --apply")
    else:
        print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
        print(f"   Исправлено проблем: {total_fixed}")
    print("=" * 80)

if __name__ == "__main__":
    main()

