#!/usr/bin/env python3
"""
Глубокий анализ конкретного турнира в базе данных
Проверяет все таблицы на наличие записей, связанных с турниром
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, Registration, JudgePayment, TournamentBudget, User
from sqlalchemy import text, and_, or_
from datetime import datetime

def analyze_tournament(tournament_name=None, tournament_date=None, tournament_id=None):
    """
    Анализирует конкретный турнир в базе данных
    
    Args:
        tournament_name: Название турнира (например, "Арена Плей Юг")
        tournament_date: Дата турнира в формате "27.11.2025" или "2025-11-27"
        tournament_id: ID турнира (если известен)
    """
    session = SessionLocal()
    
    try:
        print("=" * 80)
        print("🔍 ГЛУБОКИЙ АНАЛИЗ ТУРНИРА В БАЗЕ ДАННЫХ")
        print("=" * 80)
        print()
        
        # Поиск турнира
        tournament = None
        tournaments_found = []
        
        if tournament_id:
            tournament = session.query(Tournament).filter(
                Tournament.tournament_id == tournament_id
            ).first()
            if tournament:
                tournaments_found = [tournament]
        elif tournament_name and tournament_date:
            # Парсим дату
            try:
                if '.' in tournament_date:
                    # Формат DD.MM.YYYY
                    date_obj = datetime.strptime(tournament_date, '%d.%m.%Y').date()
                else:
                    # Формат YYYY-MM-DD
                    date_obj = datetime.strptime(tournament_date, '%Y-%m-%d').date()
                
                tournaments_found = session.query(Tournament).filter(
                    and_(
                        Tournament.name.ilike(f'%{tournament_name}%'),
                        Tournament.date == date_obj
                    )
                ).all()
                
                if tournaments_found:
                    tournament = tournaments_found[0]
            except Exception as e:
                print(f"❌ Ошибка парсинга даты: {e}")
                return
        elif tournament_name:
            tournaments_found = session.query(Tournament).filter(
                Tournament.name.ilike(f'%{tournament_name}%')
            ).all()
            if tournaments_found:
                tournament = tournaments_found[0]
        elif tournament_date:
            try:
                if '.' in tournament_date:
                    date_obj = datetime.strptime(tournament_date, '%d.%m.%Y').date()
                else:
                    date_obj = datetime.strptime(tournament_date, '%Y-%m-%d').date()
                
                tournaments_found = session.query(Tournament).filter(
                    Tournament.date == date_obj
                ).all()
                
                if tournaments_found:
                    tournament = tournaments_found[0]
            except Exception as e:
                print(f"❌ Ошибка парсинга даты: {e}")
                return
        
        # Если турнир не найден в таблице tournaments
        if not tournament:
            print("⚠️  ТУРНИР НЕ НАЙДЕН В ТАБЛИЦЕ tournaments")
            print()
            
            if tournaments_found:
                print(f"Найдено похожих турниров: {len(tournaments_found)}")
                for t in tournaments_found:
                    print(f"   - ID: {t.tournament_id}, Дата: {t.date}, Название: {t.name}")
                print()
            
            # Ищем висячие записи по дате и названию
            print("🔍 ПОИСК ВИСЯЧИХ ЗАПИСЕЙ (турнир удален, но данные остались)...")
            print()
            
            if tournament_date:
                try:
                    if '.' in tournament_date:
                        date_obj = datetime.strptime(tournament_date, '%d.%m.%Y').date()
                    else:
                        date_obj = datetime.strptime(tournament_date, '%Y-%m-%d').date()
                    
                    # Ищем регистрации с этой датой через JOIN
                    orphaned_regs = session.query(Registration).join(
                        Tournament, Registration.tournament_id == Tournament.tournament_id
                    ).filter(
                        and_(
                            Tournament.date == date_obj,
                            Tournament.name.ilike(f'%{tournament_name}%') if tournament_name else True
                        )
                    ).all()
                    
                    if orphaned_regs:
                        print(f"📝 Найдено регистраций через JOIN: {len(orphaned_regs)}")
                        for reg in orphaned_regs:
                            user = session.query(User).get(reg.user_id)
                            user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {reg.user_id}"
                            print(f"   - Registration ID: {reg.registration_id}, User: {user_name}, Status: {reg.status}")
                    else:
                        print("   ✅ Регистраций через JOIN не найдено")
                    
                    # Ищем платежи
                    orphaned_payments = session.query(JudgePayment).join(
                        Tournament, JudgePayment.tournament_id == Tournament.tournament_id
                    ).filter(
                        and_(
                            Tournament.date == date_obj,
                            Tournament.name.ilike(f'%{tournament_name}%') if tournament_name else True
                        )
                    ).all()
                    
                    if orphaned_payments:
                        print(f"💰 Найдено платежей через JOIN: {len(orphaned_payments)}")
                        for payment in orphaned_payments:
                            user = session.query(User).get(payment.user_id)
                            user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {payment.user_id}"
                            amount = payment.amount if payment.amount else "N/A"
                            is_paid = "Да" if payment.is_paid else "Нет"
                            print(f"   - Payment ID: {payment.payment_id}, User: {user_name}, Amount: {amount}, Paid: {is_paid}")
                    else:
                        print("   ✅ Платежей через JOIN не найдено")
                    
                except Exception as e:
                    print(f"❌ Ошибка при поиске висячих записей: {e}")
            
            # Ищем по tournament_id в других таблицах (если есть подозрительные ID)
            print()
            print("🔍 ПРЯМОЙ ПОИСК ПО ВСЕМ ТАБЛИЦАМ...")
            print()
            
            # Получаем все tournament_id из других таблиц
            all_reg_tournament_ids = session.query(Registration.tournament_id).distinct().all()
            all_payment_tournament_ids = session.query(JudgePayment.tournament_id).distinct().all()
            all_budget_tournament_ids = session.query(TournamentBudget.tournament_id).distinct().all()
            
            all_referenced_ids = set()
            for tid in all_reg_tournament_ids:
                all_referenced_ids.add(tid[0])
            for tid in all_payment_tournament_ids:
                all_referenced_ids.add(tid[0])
            for tid in all_budget_tournament_ids:
                all_referenced_ids.add(tid[0])
            
            # Получаем все существующие tournament_id
            existing_tournament_ids = set(
                session.query(Tournament.tournament_id).all()
            )
            existing_tournament_ids = {tid[0] for tid in existing_tournament_ids}
            
            # Находим висячие ID
            orphaned_ids = all_referenced_ids - existing_tournament_ids
            
            if orphaned_ids:
                print(f"⚠️  Найдено висячих tournament_id: {len(orphaned_ids)}")
                print(f"   ID: {sorted(orphaned_ids)}")
                print()
                
                # Для каждого висячего ID ищем записи
                for tid in sorted(orphaned_ids):
                    print(f"   📌 Tournament ID: {tid}")
                    
                    # Регистрации
                    regs = session.query(Registration).filter(
                        Registration.tournament_id == tid
                    ).all()
                    if regs:
                        print(f"      📝 Регистраций: {len(regs)}")
                        for reg in regs[:5]:
                            user = session.query(User).get(reg.user_id)
                            user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {reg.user_id}"
                            print(f"         - {user_name} (Status: {reg.status})")
                    
                    # Платежи
                    payments = session.query(JudgePayment).filter(
                        JudgePayment.tournament_id == tid
                    ).all()
                    if payments:
                        print(f"      💰 Платежей: {len(payments)}")
                        for payment in payments[:5]:
                            user = session.query(User).get(payment.user_id)
                            user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {payment.user_id}"
                            amount = payment.amount if payment.amount else "N/A"
                            print(f"         - {user_name} (Amount: {amount}, Paid: {payment.is_paid})")
                    
                    # Бюджеты
                    budgets = session.query(TournamentBudget).filter(
                        TournamentBudget.tournament_id == tid
                    ).all()
                    if budgets:
                        print(f"      💵 Бюджетов: {len(budgets)}")
                        for budget in budgets:
                            print(f"         - Budget: {budget.total_budget}, Set: {budget.budget_set_date}")
                    
                    print()
            
            return
        
        # Если турнир найден
        print("✅ ТУРНИР НАЙДЕН В ТАБЛИЦЕ tournaments")
        print(f"   ID: {tournament.tournament_id}")
        print(f"   Название: {tournament.name}")
        print(f"   Дата: {tournament.date.strftime('%d.%m.%Y')}")
        print(f"   Месяц: {tournament.month}")
        print()
        
        tournament_id = tournament.tournament_id
        
        # 1. Регистрации
        print("=" * 80)
        print("📝 РЕГИСТРАЦИИ")
        print("=" * 80)
        registrations = session.query(Registration).filter(
            Registration.tournament_id == tournament_id
        ).all()
        
        print(f"Всего регистраций: {len(registrations)}")
        print()
        
        if registrations:
            status_counts = {}
            for reg in registrations:
                status = reg.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("Статистика по статусам:")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
            print()
            
            print("Детали регистраций:")
            for reg in registrations:
                user = session.query(User).get(reg.user_id)
                user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {reg.user_id}"
                print(f"   - {user_name}: {reg.status} (Registration ID: {reg.registration_id})")
        print()
        
        # 2. Платежи
        print("=" * 80)
        print("💰 ПЛАТЕЖИ")
        print("=" * 80)
        payments = session.query(JudgePayment).filter(
            JudgePayment.tournament_id == tournament_id
        ).all()
        
        print(f"Всего платежей: {len(payments)}")
        print()
        
        if payments:
            paid_count = sum(1 for p in payments if p.is_paid)
            unpaid_count = len(payments) - paid_count
            
            print(f"Оплачено: {paid_count}")
            print(f"Не оплачено: {unpaid_count}")
            print()
            
            total_amount = sum(p.amount for p in payments if p.amount)
            print(f"Общая сумма: {total_amount} руб.")
            print()
            
            print("Детали платежей:")
            for payment in payments:
                user = session.query(User).get(payment.user_id)
                user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {payment.user_id}"
                amount = payment.amount if payment.amount else "N/A"
                is_paid = "✅ Да" if payment.is_paid else "❌ Нет"
                payment_date = payment.payment_date.strftime('%d.%m.%Y %H:%M') if payment.payment_date else "N/A"
                print(f"   - {user_name}: {amount} руб., Оплачено: {is_paid}, Дата: {payment_date}")
        print()
        
        # 3. Бюджеты
        print("=" * 80)
        print("💵 БЮДЖЕТЫ")
        print("=" * 80)
        budgets = session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id == tournament_id
        ).all()
        
        print(f"Всего бюджетов: {len(budgets)}")
        print()
        
        if budgets:
            for budget in budgets:
                print(f"   Бюджет ID: {budget.budget_id}")
                print(f"   Общий бюджет: {budget.total_budget} руб.")
                print(f"   Выплачено судьям: {budget.judges_payment if budget.judges_payment else 'N/A'} руб.")
                print(f"   Прибыль админа: {budget.admin_profit if budget.admin_profit else 'N/A'} руб.")
                print(f"   Дата установки: {budget.budget_set_date.strftime('%d.%m.%Y %H:%M')}")
                print(f"   Напоминание отправлено: {'Да' if budget.reminder_sent else 'Нет'}")
                if budget.reminder_date:
                    print(f"   Дата напоминания: {budget.reminder_date.strftime('%d.%m.%Y %H:%M')}")
                print()
        else:
            print("   Бюджет не установлен")
        print()
        
        # 4. Проверка целостности данных
        print("=" * 80)
        print("🔍 ПРОВЕРКА ЦЕЛОСТНОСТИ")
        print("=" * 80)
        
        # Проверяем, что все регистрации имеют валидных пользователей
        invalid_regs = []
        for reg in registrations:
            user = session.query(User).get(reg.user_id)
            if not user:
                invalid_regs.append(reg)
        
        if invalid_regs:
            print(f"⚠️  Найдено регистраций с несуществующими пользователями: {len(invalid_regs)}")
        else:
            print("✅ Все регистрации имеют валидных пользователей")
        
        # Проверяем, что все платежи имеют валидных пользователей
        invalid_payments = []
        for payment in payments:
            user = session.query(User).get(payment.user_id)
            if not user:
                invalid_payments.append(payment)
        
        if invalid_payments:
            print(f"⚠️  Найдено платежей с несуществующими пользователями: {len(invalid_payments)}")
        else:
            print("✅ Все платежи имеют валидных пользователей")
        
        # Проверяем соответствие регистраций и платежей
        reg_user_ids = {reg.user_id for reg in registrations}
        payment_user_ids = {payment.user_id for payment in payments}
        
        payments_without_reg = payment_user_ids - reg_user_ids
        if payments_without_reg:
            print(f"⚠️  Найдено платежей для пользователей без регистрации: {len(payments_without_reg)}")
            for user_id in payments_without_reg:
                user = session.query(User).get(user_id)
                user_name = f"{user.first_name} {user.last_name}" if user else f"User ID: {user_id}"
                print(f"   - {user_name}")
        else:
            print("✅ Все платежи соответствуют регистрациям")
        
        print()
        
        # 5. Рекомендации
        print("=" * 80)
        print("💡 РЕКОМЕНДАЦИИ")
        print("=" * 80)
        
        if len(registrations) > 0 and tournament:
            print("✅ Турнир существует в БД и имеет регистрации")
            print("   Это нормально, если турнир не был удален")
        elif len(registrations) == 0 and tournament:
            print("ℹ️  Турнир существует, но нет регистраций")
        elif not tournament and (len(orphaned_regs) > 0 if 'orphaned_regs' in locals() else False):
            print("⚠️  Турнир удален, но остались регистрации!")
            print("   Запустите: python check_orphaned_data.py --fix")
        
        print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ турнира в базе данных')
    parser.add_argument('--name', type=str, help='Название турнира (например, "Арена Плей Юг")')
    parser.add_argument('--date', type=str, help='Дата турнира (формат: DD.MM.YYYY или YYYY-MM-DD)')
    parser.add_argument('--id', type=int, help='ID турнира')
    
    args = parser.parse_args()
    
    if not args.name and not args.date and not args.id:
        # Интерактивный режим
        print("Введите данные для поиска турнира:")
        name = input("Название турнира (или Enter для пропуска): ").strip() or None
        date = input("Дата турнира (DD.MM.YYYY или Enter для пропуска): ").strip() or None
        tid = input("ID турнира (или Enter для пропуска): ").strip()
        tid = int(tid) if tid else None
        
        analyze_tournament(tournament_name=name, tournament_date=date, tournament_id=tid)
    else:
        analyze_tournament(
            tournament_name=args.name,
            tournament_date=args.date,
            tournament_id=args.id
        )


