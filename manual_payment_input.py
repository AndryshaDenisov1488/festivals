#!/usr/bin/env python3
"""
Скрипт для ручного ввода заработка судей через командную строку.
Позволяет админу ввести заработок для судьи за конкретный турнир.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User, Registration, RegistrationStatus
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from datetime import datetime

# Стандартная сумма оплаты
STANDARD_PAYMENT_AMOUNT = 5000

# Специальный судья с индивидуальной суммой
SPECIAL_JUDGE_ID = 946719504  # Лизочка Маркова
SPECIAL_JUDGE_NAME = "Лизочка Маркова"

def list_unpaid_judges():
    """Показывает список судей с неоплаченными записями"""
    session = SessionLocal()
    try:
        unpaid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == False
        ).join(User).join(Tournament).order_by(Tournament.date.desc()).all()
        
        if not unpaid_payments:
            print("✅ Нет неоплаченных записей.")
            return []
        
        # Группируем по судьям
        judges_dict = {}
        for payment in unpaid_payments:
            user_id = payment.user_id
            if user_id not in judges_dict:
                judges_dict[user_id] = {
                    'user': payment.user,
                    'payments': []
                }
            judges_dict[user_id]['payments'].append(payment)
        
        print("\n📋 СПИСОК СУДЕЙ С НЕОПЛАЧЕННЫМИ ЗАПИСЯМИ:")
        print("=" * 80)
        
        judges_list = []
        for idx, (user_id, data) in enumerate(sorted(judges_dict.items(), key=lambda x: (x[1]['user'].last_name, x[1]['user'].first_name)), 1):
            user = data['user']
            unpaid_count = len(data['payments'])
            is_special = user_id == SPECIAL_JUDGE_ID
            special_mark = " [ИНДИВИДУАЛЬНАЯ СУММА]" if is_special else ""
            
            print(f"{idx}. {user.first_name} {user.last_name} (ID: {user_id}) - {unpaid_count} неоплачено{special_mark}")
            judges_list.append((user_id, user, data['payments']))
        
        print("=" * 80)
        return judges_list
        
    finally:
        session.close()

def list_judge_tournaments(user_id):
    """Показывает список неоплаченных турниров для судьи"""
    session = SessionLocal()
    try:
        unpaid_payments = session.query(JudgePayment).filter(
            and_(
                JudgePayment.user_id == user_id,
                JudgePayment.is_paid == False
            )
        ).join(Tournament).order_by(Tournament.date.desc()).all()
        
        if not unpaid_payments:
            print("✅ Нет неоплаченных записей для этого судьи.")
            return []
        
        print(f"\n📋 НЕОПЛАЧЕННЫЕ ТУРНИРЫ ДЛЯ {unpaid_payments[0].user.first_name} {unpaid_payments[0].user.last_name}:")
        print("=" * 80)
        
        tournaments_list = []
        for idx, payment in enumerate(unpaid_payments, 1):
            print(f"{idx}. {payment.tournament.date.strftime('%d.%m.%Y')} - {payment.tournament.name} (ID: {payment.payment_id})")
            tournaments_list.append(payment)
        
        print("=" * 80)
        return tournaments_list
        
    finally:
        session.close()

def input_payment(payment_id, amount):
    """Вводит заработок для записи об оплате"""
    session = SessionLocal()
    try:
        payment = session.query(JudgePayment).options(
            joinedload(JudgePayment.user),
            joinedload(JudgePayment.tournament)
        ).filter(JudgePayment.payment_id == payment_id).first()
        
        if not payment:
            print(f"❌ Запись об оплате с ID {payment_id} не найдена.")
            return False
        
        if payment.is_paid:
            print(f"⚠️  Эта запись уже оплачена (сумма: {payment.amount} руб.).")
            response = input("Перезаписать? (yes/no): ")
            if response.lower() not in ['yes', 'y', 'да', 'д']:
                print("Отменено.")
                return False
        
        # Проверка суммы
        is_special_judge = payment.user_id == SPECIAL_JUDGE_ID
        
        if not is_special_judge:
            MIN_PAYMENT_AMOUNT = 3500
            if amount < MIN_PAYMENT_AMOUNT:
                print(f"❌ Минимальная сумма оплаты составляет {MIN_PAYMENT_AMOUNT} рублей.")
                return False
            
            if amount != STANDARD_PAYMENT_AMOUNT:
                print(f"⚠️  Внимание! Стандартная сумма для всех судей (кроме {SPECIAL_JUDGE_NAME}) составляет {STANDARD_PAYMENT_AMOUNT} руб.")
                print(f"Вы вводите {amount} руб.")
                response = input("Продолжить? (yes/no): ")
                if response.lower() not in ['yes', 'y', 'да', 'д']:
                    print("Отменено.")
                    return False
        
        # Сохраняем заработок
        payment.is_paid = True
        payment.amount = amount
        payment.payment_date = datetime.now()
        
        session.commit()
        
        print(f"\n✅ Заработок успешно введен!")
        print(f"   Судья: {payment.user.first_name} {payment.user.last_name}")
        print(f"   Турнир: {payment.tournament.name}")
        print(f"   Дата: {payment.tournament.date.strftime('%d.%m.%Y')}")
        print(f"   Сумма: {amount} руб.")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при вводе заработка: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def interactive_input():
    """Интерактивный ввод заработка"""
    print("=" * 80)
    print("💰 РУЧНОЙ ВВОД ЗАРАБОТКА СУДЕЙ")
    print("=" * 80)
    print()
    
    # Показываем список судей
    judges_list = list_unpaid_judges()
    
    if not judges_list:
        return
    
    # Выбор судьи
    try:
        judge_idx = int(input("\nВыберите номер судьи (или 0 для выхода): "))
        if judge_idx == 0:
            print("Отменено.")
            return
        
        if judge_idx < 1 or judge_idx > len(judges_list):
            print("❌ Неверный номер.")
            return
        
        user_id, user, payments = judges_list[judge_idx - 1]
        is_special = user_id == SPECIAL_JUDGE_ID
        
        # Показываем турниры
        tournaments_list = list_judge_tournaments(user_id)
        
        if not tournaments_list:
            return
        
        # Выбор турнира
        tournament_idx = int(input("\nВыберите номер турнира (или 0 для выхода): "))
        if tournament_idx == 0:
            print("Отменено.")
            return
        
        if tournament_idx < 1 or tournament_idx > len(tournaments_list):
            print("❌ Неверный номер.")
            return
        
        payment = tournaments_list[tournament_idx - 1]
        
        # Ввод суммы
        if is_special:
            print(f"\n💰 Ввод заработка для {SPECIAL_JUDGE_NAME} (индивидуальная сумма)")
        else:
            print(f"\n💰 Ввод заработка (стандартная сумма: {STANDARD_PAYMENT_AMOUNT} руб.)")
        
        amount_str = input("Введите сумму заработка: ")
        try:
            amount = float(amount_str.strip().replace(',', '.'))
        except ValueError:
            print("❌ Неверный формат суммы.")
            return
        
        # Ввод заработка
        input_payment(payment.payment_id, amount)
        
    except ValueError:
        print("❌ Неверный формат ввода.")
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def direct_input(payment_id, amount):
    """Прямой ввод заработка (для использования в других скриптах)"""
    return input_payment(payment_id, amount)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        # Прямой ввод через аргументы командной строки
        try:
            payment_id = int(sys.argv[1])
            amount = float(sys.argv[2])
            direct_input(payment_id, amount)
        except ValueError:
            print("❌ Неверный формат аргументов.")
            print("Использование: python manual_payment_input.py [payment_id] [amount]")
            print("Или запустите без аргументов для интерактивного режима.")
    else:
        # Интерактивный режим
        interactive_input()

