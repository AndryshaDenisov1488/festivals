#!/usr/bin/env python3
"""
Упрощенный скрипт для принудительной отправки напоминаний об оплате
Показывает список судей, которым нужно отправить напоминания
"""

import sys
import os
from datetime import datetime, timezone

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User
from sqlalchemy import and_

def show_unpaid_judges():
    """Показывает список неоплаченных судей тестового турнира"""
    
    session = SessionLocal()
    try:
        print("🔍 АНАЛИЗ НЕОПЛАЧЕННЫХ СУДЕЙ ТЕСТОВОГО ТУРНИРА")
        print("=" * 60)
        
        # Находим тестовый турнир
        test_tournament = session.query(Tournament).filter(
            Tournament.name.like("%Тестовый%")
        ).first()
        
        if not test_tournament:
            print("❌ Тестовый турнир не найден!")
            return
        
        print(f"🏆 Турнир: {test_tournament.name}")
        print(f"📅 Дата: {test_tournament.date.strftime('%d.%m.%Y')}")
        print()
        
        # Находим всех судей этого турнира
        all_payments = session.query(JudgePayment).join(User).filter(
            JudgePayment.tournament_id == test_tournament.tournament_id
        ).all()
        
        print(f"👥 Всего судей в турнире: {len(all_payments)}")
        print()
        
        # Разделяем на оплаченных и неоплаченных
        paid_judges = []
        unpaid_judges = []
        
        for payment in all_payments:
            if payment.is_paid:
                paid_judges.append(payment)
            else:
                unpaid_judges.append(payment)
        
        print("✅ ОПЛАЧЕННЫЕ СУДЬИ:")
        if paid_judges:
            for payment in paid_judges:
                amount = payment.amount if payment.amount else "Не указана"
                date = payment.payment_date.strftime('%d.%m.%Y %H:%M') if payment.payment_date else "Не указана"
                print(f"   👤 {payment.user.first_name} {payment.user.last_name}")
                print(f"      💵 Сумма: {amount} руб.")
                print(f"      📅 Дата оплаты: {date}")
        else:
            print("   Нет оплаченных судей")
        
        print()
        print("❌ НЕОПЛАЧЕННЫЕ СУДЬИ:")
        if unpaid_judges:
            for payment in unpaid_judges:
                reminder_status = "Отправлено" if payment.reminder_sent else "Не отправлено"
                last_reminder = payment.reminder_date.strftime('%d.%m.%Y %H:%M') if payment.reminder_date else "Не отправлялось"
                print(f"   👤 {payment.user.first_name} {payment.user.last_name}")
                print(f"      📧 Напоминание: {reminder_status}")
                print(f"      📅 Последнее напоминание: {last_reminder}")
                print(f"      🆔 ID платежа: {payment.payment_id}")
        else:
            print("   Все судьи оплачены!")
        
        print()
        print("📊 СТАТИСТИКА:")
        print(f"   ✅ Оплачено: {len(paid_judges)} судей")
        print(f"   ❌ Не оплачено: {len(unpaid_judges)} судей")
        print(f"   👥 Всего: {len(all_payments)} судей")
        
        if unpaid_judges:
            print()
            print("💡 РЕКОМЕНДАЦИИ:")
            print("   1. Запустите основной скрипт: python force_send_payment_reminders.py")
            print("   2. Или отправьте напоминания вручную через бота")
            print("   3. Проверьте, что судьи получают сообщения")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

def main():
    """Главная функция"""
    print("🔧 УПРОЩЕННЫЙ СКРИПТ АНАЛИЗА НЕОПЛАЧЕННЫХ СУДЕЙ")
    print("=" * 60)
    print("Этот скрипт покажет список неоплаченных судей")
    print("тестового турнира без отправки сообщений.")
    print()
    
    show_unpaid_judges()

if __name__ == "__main__":
    main()
