#!/usr/bin/env python3
"""
Скрипт для массового обновления заработка судей.
Помечает все неоплаченные записи как оплаченные и устанавливает заработок:
- 5000 руб. для всех судей (кроме Лизочки Марковой)
- 7000 руб. для Лизочки Марковой (ID: 946719504)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, User, Tournament
from sqlalchemy import and_
from datetime import datetime

# Стандартная сумма оплаты
STANDARD_PAYMENT_AMOUNT = 5000

# Специальный судья с индивидуальной суммой
SPECIAL_JUDGE_ID = 946719504  # Лизочка Маркова
SPECIAL_JUDGE_AMOUNT = 7000

def update_all_unpaid_payments(dry_run=True):
    """Обновляет все неоплаченные записи"""
    session = SessionLocal()
    try:
        # Получаем все неоплаченные записи
        unpaid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == False
        ).join(User).join(Tournament).order_by(
            User.last_name, User.first_name, Tournament.date
        ).all()
        
        if not unpaid_payments:
            print("✅ Нет неоплаченных записей.")
            return
        
        print(f"\n📋 Найдено неоплаченных записей: {len(unpaid_payments)}")
        print("=" * 80)
        
        # Группируем по судьям для статистики
        judges_stats = {}
        updates = []
        
        for payment in unpaid_payments:
            user_id = payment.user_id
            is_special = user_id == SPECIAL_JUDGE_ID
            amount = SPECIAL_JUDGE_AMOUNT if is_special else STANDARD_PAYMENT_AMOUNT
            
            # Статистика
            if user_id not in judges_stats:
                judges_stats[user_id] = {
                    'user': payment.user,
                    'count': 0,
                    'total_amount': 0,
                    'is_special': is_special
                }
            judges_stats[user_id]['count'] += 1
            judges_stats[user_id]['total_amount'] += amount
            
            # Подготовка обновления
            updates.append({
                'payment': payment,
                'amount': amount,
                'is_special': is_special
            })
        
        # Выводим статистику
        print("\n📊 СТАТИСТИКА ПО СУДЬЯМ:")
        print("=" * 80)
        
        for user_id, stats in sorted(judges_stats.items(), key=lambda x: (x[1]['user'].last_name, x[1]['user'].first_name)):
            user = stats['user']
            special_mark = " [ИНДИВИДУАЛЬНАЯ СУММА]" if stats['is_special'] else ""
            print(f"👤 {user.first_name} {user.last_name} (ID: {user_id}){special_mark}")
            print(f"   📋 Записей: {stats['count']}")
            print(f"   💰 Сумма за запись: {SPECIAL_JUDGE_AMOUNT if stats['is_special'] else STANDARD_PAYMENT_AMOUNT} руб.")
            print(f"   💰 Общая сумма: {stats['total_amount']} руб.")
            print()
        
        # Общая статистика
        total_count = len(updates)
        total_amount = sum(u['amount'] for u in updates)
        special_count = sum(1 for u in updates if u['is_special'])
        standard_count = total_count - special_count
        
        print("=" * 80)
        print(f"📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего записей: {total_count}")
        print(f"   Стандартных (5000 руб.): {standard_count}")
        print(f"   Индивидуальных (7000 руб.): {special_count}")
        print(f"   💰 Общая сумма: {total_amount} руб.")
        print("=" * 80)
        
        if dry_run:
            print("\n⚠️  РЕЖИМ ПРОВЕРКИ (dry-run)")
            print("   Изменения НЕ будут сохранены.")
            print("   Для применения изменений запустите скрипт с флагом --apply")
            return
        
        # Подтверждение
        print("\n⚠️  ВНИМАНИЕ!")
        print(f"   Будет обновлено {total_count} записей.")
        print(f"   Общая сумма: {total_amount} руб.")
        print()
        response = input("Продолжить? (yes/no): ")
        
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("❌ Отменено.")
            return
        
        # Применяем обновления
        print("\n🔄 Обновление записей...")
        
        updated_count = 0
        for update in updates:
            payment = update['payment']
            amount = update['amount']
            
            payment.is_paid = True
            payment.amount = amount
            payment.payment_date = datetime.now()
            
            updated_count += 1
            if updated_count % 10 == 0:
                print(f"   Обновлено: {updated_count}/{total_count}")
        
        session.commit()
        
        print(f"\n✅ Успешно обновлено {updated_count} записей!")
        print(f"💰 Общая сумма: {total_amount} руб.")
        
        # Детальная информация по судьям
        print("\n📋 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
        print("=" * 80)
        
        for user_id, stats in sorted(judges_stats.items(), key=lambda x: (x[1]['user'].last_name, x[1]['user'].first_name)):
            user = stats['user']
            special_mark = " [ИНДИВИДУАЛЬНАЯ СУММА]" if stats['is_special'] else ""
            print(f"✅ {user.first_name} {user.last_name}{special_mark}")
            print(f"   Обновлено записей: {stats['count']}")
            print(f"   Общая сумма: {stats['total_amount']} руб.")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

def main():
    """Основная функция"""
    print("=" * 80)
    print("💰 МАССОВОЕ ОБНОВЛЕНИЕ ЗАРАБОТКА СУДЕЙ")
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
        print("   Для применения изменений используйте: python mass_update_payments.py --apply")
        print()
    
    update_all_unpaid_payments(dry_run=dry_run)
    
    print()
    print("=" * 80)
    print("✅ ЗАВЕРШЕНО")
    print("=" * 80)

if __name__ == "__main__":
    main()

