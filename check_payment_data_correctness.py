#!/usr/bin/env python3
"""
Скрипт для проверки правильности ввода данных об оплате от судей.
Проверяет:
1. Правильность сумм (должна быть 5000 для всех, кроме Лизочки Марковой)
2. Наличие данных об оплате для утвержденных судей
3. Некорректные суммы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User, Registration, RegistrationStatus
from sqlalchemy import and_, or_, func
from datetime import datetime

# Стандартная сумма оплаты
STANDARD_PAYMENT_AMOUNT = 5000

# Специальный судья с индивидуальной суммой
SPECIAL_JUDGE_ID = 946719504  # Лизочка Маркова
SPECIAL_JUDGE_NAME = "Лизочка Маркова"

def check_payment_data_correctness():
    """Проверяет правильность данных об оплате"""
    print("=" * 80)
    print("🔍 ПРОВЕРКА ПРАВИЛЬНОСТИ ДАННЫХ ОБ ОПЛАТЕ")
    print(f"📅 Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 80)
    print()
    
    session = SessionLocal()
    output_lines = []
    
    def log(text):
        output_lines.append(text)
        print(text)
    
    try:
        # 1. Проверка сумм оплаты
        log("1️⃣ ПРОВЕРКА СУММ ОПЛАТЫ")
        log("-" * 80)
        
        # Получаем все оплаченные записи
        paid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == True
        ).join(Tournament).join(User).order_by(Tournament.date.desc()).all()
        
        incorrect_amounts = []
        missing_amounts = []
        correct_amounts = []
        
        for payment in paid_payments:
            if payment.amount is None:
                missing_amounts.append(payment)
            elif payment.user_id == SPECIAL_JUDGE_ID:
                # Для Лизочки Марковой - индивидуальная сумма (любая)
                correct_amounts.append(payment)
            elif payment.amount != STANDARD_PAYMENT_AMOUNT:
                incorrect_amounts.append(payment)
            else:
                correct_amounts.append(payment)
        
        log(f"   Всего оплаченных записей: {len(paid_payments)}")
        log(f"   ✅ Правильные суммы: {len(correct_amounts)}")
        log(f"   ⚠️  Неправильные суммы: {len(incorrect_amounts)}")
        log(f"   ❌ Отсутствуют суммы: {len(missing_amounts)}")
        log("")
        
        if incorrect_amounts:
            log(f"   📋 СПИСОК ЗАПИСЕЙ С НЕПРАВИЛЬНЫМИ СУММАМИ ({len(incorrect_amounts)}):")
            log("")
            for payment in incorrect_amounts:
                expected = STANDARD_PAYMENT_AMOUNT
                log(f"   ⚠️ {payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                log(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                log(f"      Текущая сумма: {payment.amount} руб.")
                log(f"      Ожидаемая сумма: {expected} руб.")
                log(f"      Разница: {expected - payment.amount} руб.")
                log("")
        
        if missing_amounts:
            log(f"   📋 СПИСОК ЗАПИСЕЙ БЕЗ СУММЫ ({len(missing_amounts)}):")
            log("")
            for payment in missing_amounts:
                expected = STANDARD_PAYMENT_AMOUNT if payment.user_id != SPECIAL_JUDGE_ID else "индивидуальная"
                log(f"   ❌ {payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                log(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                log(f"      Сумма: НЕ УКАЗАНА")
                log(f"      Ожидаемая сумма: {expected} руб." if expected != "индивидуальная" else f"      Ожидаемая сумма: {expected}")
                log("")
        
        # 2. Проверка данных для Лизочки Марковой
        log("2️⃣ ПРОВЕРКА ДАННЫХ ДЛЯ ЛИЗОЧКИ МАРКОВОЙ")
        log("-" * 80)
        
        lizochka_payments = session.query(JudgePayment).filter(
            and_(
                JudgePayment.user_id == SPECIAL_JUDGE_ID,
                JudgePayment.is_paid == True
            )
        ).join(Tournament).order_by(Tournament.date.desc()).all()
        
        if lizochka_payments:
            log(f"   Найдено оплаченных записей для {SPECIAL_JUDGE_NAME}: {len(lizochka_payments)}")
            log("")
            for payment in lizochka_payments:
                amount_text = f"{payment.amount} руб." if payment.amount else "НЕ УКАЗАНА"
                log(f"   📅 {payment.tournament.date.strftime('%d.%m.%Y')} - {payment.tournament.name}")
                log(f"      Сумма: {amount_text}")
                if payment.amount is None:
                    log(f"      ⚠️ Требуется ввод суммы вручную")
                log("")
        else:
            log(f"   ✅ Нет оплаченных записей для {SPECIAL_JUDGE_NAME}")
            log("")
        
        # 3. Проверка отсутствующих данных об оплате
        log("3️⃣ ПРОВЕРКА ОТСУТСТВУЮЩИХ ДАННЫХ ОБ ОПЛАТЕ")
        log("-" * 80)
        
        # Находим утвержденных судей без записей об оплате
        approved_registrations = session.query(Registration).filter(
            Registration.status == RegistrationStatus.APPROVED
        ).all()
        
        missing_payments = []
        for registration in approved_registrations:
            payment = session.query(JudgePayment).filter(
                and_(
                    JudgePayment.user_id == registration.user_id,
                    JudgePayment.tournament_id == registration.tournament_id
                )
            ).first()
            
            if not payment:
                missing_payments.append(registration)
        
        if missing_payments:
            log(f"   Найдено утвержденных регистраций без записей об оплате: {len(missing_payments)}")
            log("")
            
            # Группируем по турнирам
            by_tournament = {}
            for reg in missing_payments:
                t_id = reg.tournament_id
                if t_id not in by_tournament:
                    by_tournament[t_id] = {
                        'tournament': reg.tournament,
                        'judges': []
                    }
                by_tournament[t_id]['judges'].append(reg.user)
            
            for t_id, data in sorted(by_tournament.items(), key=lambda x: x[1]['tournament'].date, reverse=True):
                tournament = data['tournament']
                judges = data['judges']
                
                log(f"   🏆 Турнир: {tournament.name} ({tournament.date.strftime('%d.%m.%Y')})")
                log(f"   👥 Судьи без записей об оплате: {len(judges)}")
                for judge in judges:
                    log(f"      - {judge.first_name} {judge.last_name} (ID: {judge.user_id})")
                log("")
        else:
            log("   ✅ Все утвержденные регистрации имеют записи об оплате")
            log("")
        
        # 4. Статистика
        log("4️⃣ СТАТИСТИКА")
        log("-" * 80)
        
        total_paid = len(paid_payments)
        total_correct = len(correct_amounts)
        total_incorrect = len(incorrect_amounts) + len(missing_amounts)
        
        log(f"   Всего оплаченных записей: {total_paid}")
        log(f"   ✅ Правильных: {total_correct} ({total_correct/total_paid*100:.1f}%)" if total_paid > 0 else "   ✅ Правильных: 0")
        log(f"   ⚠️  Требуют исправления: {total_incorrect} ({total_incorrect/total_paid*100:.1f}%)" if total_paid > 0 else "   ⚠️  Требуют исправления: 0")
        log("")
        
        # 5. Рекомендации
        log("5️⃣ РЕКОМЕНДАЦИИ")
        log("-" * 80)
        
        if incorrect_amounts or missing_amounts:
            log("   Для исправления проблем:")
            log("")
            if incorrect_amounts:
                log(f"   1. Исправить {len(incorrect_amounts)} записей с неправильными суммами")
                log("      Используйте админскую команду в боте или SQL:")
                log("      UPDATE judge_payments SET amount = 5000 WHERE payment_id = <id>;")
                log("")
            if missing_amounts:
                log(f"   2. Ввести суммы для {len(missing_amounts)} записей без суммы")
                log("      Для Лизочки Марковой используйте админскую команду в боте")
                log("      Для остальных: UPDATE judge_payments SET amount = 5000 WHERE payment_id = <id>;")
                log("")
        else:
            log("   ✅ Все данные корректны!")
            log("")
        
        log("=" * 80)
        log("✅ Проверка завершена")
        log("=" * 80)
        
        # Сохраняем в файл
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"payment_correctness_check_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        log(f"\n💾 Отчет сохранен в файл: {filename}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка при проверке: {e}"
        log(error_msg)
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_payment_data_correctness()

