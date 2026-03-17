#!/usr/bin/env python3
"""
Скрипт для анализа проблем с оплатами судей в базе данных.
Показывает все нюансы: кто не ввел данные об оплате, кто ввел некорректные данные и т.д.
Сохраняет отчет в файл.
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import JudgePayment, Tournament, User, Registration, RegistrationStatus
from sqlalchemy import and_, or_, func

# Минимальная сумма оплаты
MIN_PAYMENT_AMOUNT = 3500

def analyze_payment_issues(save_to_file=True):
    """Анализирует проблемы с оплатами"""
    output_lines = []
    
    def log(text):
        """Добавляет текст в вывод и выводит на экран"""
        output_lines.append(text)
        print(text)
    
    log("=" * 80)
    log("🔍 АНАЛИЗ ПРОБЛЕМ С ОПЛАТАМИ СУДЕЙ")
    log(f"📅 Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    log("=" * 80)
    log("")
    
    session = SessionLocal()
    try:
        # 1. Неоплаченные записи
        log("1️⃣ НЕОПЛАЧЕННЫЕ ЗАПИСИ ОБ ОПЛАТЕ")
        log("-" * 80)
        unpaid_payments = session.query(JudgePayment).filter(
            JudgePayment.is_paid == False
        ).join(Tournament).join(User).order_by(Tournament.date.desc()).all()
        
        if unpaid_payments:
            log(f"   Найдено неоплаченных записей: {len(unpaid_payments)}\n")
            
            # Группируем по турнирам
            by_tournament = {}
            for payment in unpaid_payments:
                t_id = payment.tournament_id
                if t_id not in by_tournament:
                    by_tournament[t_id] = {
                        'tournament': payment.tournament,
                        'payments': []
                    }
                by_tournament[t_id]['payments'].append(payment)
            
            for t_id, data in sorted(by_tournament.items(), key=lambda x: x[1]['tournament'].date, reverse=True):
                tournament = data['tournament']
                payments = data['payments']
                
                log(f"   🏆 Турнир: {tournament.name}")
                log(f"   📅 Дата: {tournament.date.strftime('%d.%m.%Y')}")
                log(f"   👥 Неоплаченных судей: {len(payments)}")
                
                for payment in payments:
                    # Проверяем, существует ли регистрация
                    registration = session.query(Registration).filter(
                        and_(
                            Registration.user_id == payment.user_id,
                            Registration.tournament_id == payment.tournament_id,
                            Registration.status == RegistrationStatus.APPROVED
                        )
                    ).first()
                    
                    status_icon = "✅" if registration else "⚠️"
                    status_text = "утвержден" if registration else "НЕ УТВЕРЖДЕН (проблема!)"
                    
                    reminder_info = ""
                    if payment.reminder_sent:
                        reminder_info = f", напоминание отправлено {payment.reminder_date.strftime('%d.%m.%Y %H:%M') if payment.reminder_date else 'N/A'}"
                    
                    log(f"      {status_icon} {payment.user.first_name} {payment.user.last_name} "
                          f"(ID: {payment.user.user_id}) - {status_text}{reminder_info}")
                
                log("")
        else:
            log("   ✅ Все записи об оплате оплачены!\n")
        
        # 2. Некорректные суммы оплаты
        log("2️⃣ НЕКОРРЕКТНЫЕ СУММЫ ОПЛАТЫ")
        log("-" * 80)
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
            log(f"   Найдено записей с некорректными суммами: {len(incorrect_amounts)}\n")
            
            for payment in incorrect_amounts:
                amount_text = f"{payment.amount} руб." if payment.amount else "НЕ УКАЗАНА"
                log(f"   ⚠️ {payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                log(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                log(f"      Сумма: {amount_text}")
                if payment.amount and payment.amount < MIN_PAYMENT_AMOUNT:
                    log(f"      ❌ Сумма меньше минимальной ({MIN_PAYMENT_AMOUNT} руб.)")
                elif payment.amount is None:
                    log(f"      ❌ Сумма не указана")
                log("")
        else:
            log("   ✅ Все суммы оплаты корректны!\n")
        
        # 3. Записи об оплате для неутвержденных судей
        log("3️⃣ ЗАПИСИ ОБ ОПЛАТЕ ДЛЯ НЕУТВЕРЖДЕННЫХ СУДЕЙ")
        log("-" * 80)
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
            log(f"   Найдено записей об оплате для неутвержденных судей: {len(orphaned_payments)}\n")
            
            for payment in orphaned_payments:
                # Проверяем, существует ли регистрация вообще
                any_registration = session.query(Registration).filter(
                    and_(
                        Registration.user_id == payment.user_id,
                        Registration.tournament_id == payment.tournament_id
                    )
                ).first()
                
                if any_registration:
                    status_text = f"статус: {any_registration.status}"
                else:
                    status_text = "регистрация удалена"
                
                log(f"   ⚠️ {payment.user.first_name} {payment.user.last_name} (ID: {payment.user.user_id})")
                log(f"      Турнир: {payment.tournament.name} ({payment.tournament.date.strftime('%d.%m.%Y')})")
                log(f"      Проблема: {status_text}")
                log(f"      Оплачено: {'Да' if payment.is_paid else 'Нет'}")
                if payment.is_paid and payment.amount:
                    log(f"      Сумма: {payment.amount} руб.")
                log("")
        else:
            log("   ✅ Все записи об оплате соответствуют утвержденным регистрациям!\n")
        
        # 4. Статистика по турнирам
        log("4️⃣ СТАТИСТИКА ПО ТУРНИРАМ")
        log("-" * 80)
        
        # Группируем по турнирам
        tournaments_stats = {}
        all_payments = session.query(JudgePayment).join(Tournament).all()
        
        for payment in all_payments:
            t_id = payment.tournament_id
            if t_id not in tournaments_stats:
                tournaments_stats[t_id] = {
                    'tournament': payment.tournament,
                    'total': 0,
                    'paid': 0,
                    'unpaid': 0,
                    'incorrect_amount': 0,
                    'orphaned': 0
                }
            
            stats = tournaments_stats[t_id]
            stats['total'] += 1
            
            if payment.is_paid:
                stats['paid'] += 1
                if payment.amount is None or payment.amount < MIN_PAYMENT_AMOUNT:
                    stats['incorrect_amount'] += 1
            else:
                stats['unpaid'] += 1
            
            # Проверяем, утвержден ли судья
            registration = session.query(Registration).filter(
                and_(
                    Registration.user_id == payment.user_id,
                    Registration.tournament_id == payment.tournament_id,
                    Registration.status == RegistrationStatus.APPROVED
                )
            ).first()
            
            if not registration:
                stats['orphaned'] += 1
        
        # Сортируем по дате
        sorted_tournaments = sorted(tournaments_stats.items(), key=lambda x: x[1]['tournament'].date, reverse=True)
        
        log(f"   Всего турниров с записями об оплате: {len(sorted_tournaments)}\n")
        
        for t_id, stats in sorted_tournaments[:20]:  # Показываем последние 20
            tournament = stats['tournament']
            issues = []
            
            if stats['unpaid'] > 0:
                issues.append(f"{stats['unpaid']} неоплачено")
            if stats['incorrect_amount'] > 0:
                issues.append(f"{stats['incorrect_amount']} некорректная сумма")
            if stats['orphaned'] > 0:
                issues.append(f"{stats['orphaned']} неутвержденных")
            
            issue_text = f" ⚠️ ({', '.join(issues)})" if issues else " ✅"
            
            log(f"   {tournament.date.strftime('%d.%m.%Y')} - {tournament.name}")
            log(f"      Всего: {stats['total']}, Оплачено: {stats['paid']}, Неоплачено: {stats['unpaid']}{issue_text}")
        
        if len(sorted_tournaments) > 20:
            log(f"\n   ... и еще {len(sorted_tournaments) - 20} турниров")
        
        log("")
        
        # 5. Общая статистика
        log("5️⃣ ОБЩАЯ СТАТИСТИКА")
        log("-" * 80)
        
        total_payments = session.query(JudgePayment).count()
        paid_payments = session.query(JudgePayment).filter(JudgePayment.is_paid == True).count()
        unpaid_payments = session.query(JudgePayment).filter(JudgePayment.is_paid == False).count()
        
        log(f"   Всего записей об оплате: {total_payments}")
        log(f"   Оплачено: {paid_payments} ({paid_payments/total_payments*100:.1f}%)" if total_payments > 0 else "   Оплачено: 0")
        log(f"   Неоплачено: {unpaid_payments} ({unpaid_payments/total_payments*100:.1f}%)" if total_payments > 0 else "   Неоплачено: 0")
        
        # Суммы
        total_amount = session.query(func.sum(JudgePayment.amount)).filter(
            and_(
                JudgePayment.is_paid == True,
                JudgePayment.amount.isnot(None)
            )
        ).scalar() or 0
        
        avg_amount = session.query(func.avg(JudgePayment.amount)).filter(
            and_(
                JudgePayment.is_paid == True,
                JudgePayment.amount.isnot(None),
                JudgePayment.amount >= MIN_PAYMENT_AMOUNT
            )
        ).scalar() or 0
        
        log(f"   Общая сумма оплат: {total_amount:,.0f} руб.")
        log(f"   Средняя сумма (корректная): {avg_amount:,.0f} руб." if avg_amount > 0 else "   Средняя сумма: N/A")
        
        log("")
        log("=" * 80)
        log("✅ Анализ завершен")
        log("=" * 80)
        
        # Сохраняем в файл
        if save_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"payment_analysis_report_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            log(f"\n💾 Отчет сохранен в файл: {filename}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка при анализе: {e}"
        log(error_msg)
        import traceback
        traceback.print_exc()
        if save_to_file:
            output_lines.append("\n" + traceback.format_exc())
    finally:
        session.close()
        if save_to_file and output_lines:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"payment_analysis_report_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output_lines))
                print(f"\n💾 Отчет сохранен в файл: {filename}")
            except Exception as e:
                print(f"\n⚠️ Не удалось сохранить отчет в файл: {e}")

if __name__ == "__main__":
    analyze_payment_issues(save_to_file=True)
