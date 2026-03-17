#!/usr/bin/env python3
"""
Принудительное удаление турнира и всех связанных данных
Используется для удаления турнира, который не удалился через бота
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Tournament, Registration, JudgePayment, TournamentBudget, User
from sqlalchemy import text

def delete_tournament_force(tournament_name=None, tournament_date=None, tournament_id=None):
    """
    Принудительно удаляет турнир и все связанные данные
    
    Args:
        tournament_name: Название турнира
        tournament_date: Дата турнира (DD.MM.YYYY)
        tournament_id: ID турнира
    """
    session = SessionLocal()
    
    try:
        print("=" * 80)
        print("🗑️  ПРИНУДИТЕЛЬНОЕ УДАЛЕНИЕ ТУРНИРА")
        print("=" * 80)
        print()
        
        # Поиск турнира
        tournament = None
        
        if tournament_id:
            tournament = session.query(Tournament).filter(
                Tournament.tournament_id == tournament_id
            ).first()
        elif tournament_name and tournament_date:
            from datetime import datetime
            try:
                if '.' in tournament_date:
                    date_obj = datetime.strptime(tournament_date, '%d.%m.%Y').date()
                else:
                    date_obj = datetime.strptime(tournament_date, '%Y-%m-%d').date()
                
                tournament = session.query(Tournament).filter(
                    and_(
                        Tournament.name.ilike(f'%{tournament_name}%'),
                        Tournament.date == date_obj
                    )
                ).first()
            except Exception as e:
                print(f"❌ Ошибка парсинга даты: {e}")
                return False
        elif tournament_name:
            tournaments = session.query(Tournament).filter(
                Tournament.name.ilike(f'%{tournament_name}%')
            ).all()
            if len(tournaments) == 1:
                tournament = tournaments[0]
            elif len(tournaments) > 1:
                print(f"⚠️  Найдено несколько турниров с таким названием:")
                for t in tournaments:
                    print(f"   - ID: {t.tournament_id}, Дата: {t.date.strftime('%d.%m.%Y')}, Название: {t.name}")
                print()
                tid = input("Введите ID турнира для удаления: ").strip()
                try:
                    tournament_id = int(tid)
                    tournament = session.query(Tournament).filter(
                        Tournament.tournament_id == tournament_id
                    ).first()
                except:
                    print("❌ Неверный ID")
                    return False
        
        if not tournament:
            print("❌ Турнир не найден!")
            return False
        
        print(f"✅ Найден турнир:")
        print(f"   ID: {tournament.tournament_id}")
        print(f"   Название: {tournament.name}")
        print(f"   Дата: {tournament.date.strftime('%d.%m.%Y')}")
        print(f"   Месяц: {tournament.month}")
        print()
        
        tournament_id = tournament.tournament_id
        
        # Подсчитываем данные для удаления
        registrations_count = session.query(Registration).filter(
            Registration.tournament_id == tournament_id
        ).count()
        
        payments_count = session.query(JudgePayment).filter(
            JudgePayment.tournament_id == tournament_id
        ).count()
        
        budgets_count = session.query(TournamentBudget).filter(
            TournamentBudget.tournament_id == tournament_id
        ).count()
        
        print("📊 ДАННЫЕ ДЛЯ УДАЛЕНИЯ:")
        print(f"   📝 Регистраций: {registrations_count}")
        print(f"   💰 Платежей: {payments_count}")
        print(f"   💵 Бюджетов: {budgets_count}")
        print()
        
        print("⚠️  ВНИМАНИЕ: Это действие необратимо!")
        print("Все данные о турнире будут удалены навсегда.")
        print()
        
        confirm = input("Продолжить удаление? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y', 'да']:
            print("❌ Операция отменена")
            return False
        
        print()
        print("🗑️  НАЧИНАЕМ УДАЛЕНИЕ...")
        print()
        
        deleted_count = 0
        
        # 1. Удаляем записи об оплате
        if payments_count > 0:
            deleted_payments = session.query(JudgePayment).filter(
                JudgePayment.tournament_id == tournament_id
            ).delete(synchronize_session=False)
            deleted_count += deleted_payments
            print(f"✅ Удалено записей об оплате: {deleted_payments}")
        
        # 2. Удаляем бюджет турнира
        if budgets_count > 0:
            deleted_budgets = session.query(TournamentBudget).filter(
                TournamentBudget.tournament_id == tournament_id
            ).delete(synchronize_session=False)
            deleted_count += deleted_budgets
            print(f"✅ Удалено записей бюджета: {deleted_budgets}")
        
        # 3. Удаляем регистрации
        if registrations_count > 0:
            deleted_registrations = session.query(Registration).filter(
                Registration.tournament_id == tournament_id
            ).delete(synchronize_session=False)
            deleted_count += deleted_registrations
            print(f"✅ Удалено регистраций: {deleted_registrations}")
        
        # 4. Удаляем сам турнир
        tournament_name = tournament.name
        tournament_date_str = tournament.date.strftime('%d.%m.%Y')
        session.delete(tournament)
        deleted_count += 1
        print(f"✅ Удален турнир: {tournament_name} ({tournament_date_str})")
        
        # Коммитим изменения
        session.commit()
        
        print()
        print(f"✅ Всего удалено записей: {deleted_count}")
        print("✅ Турнир и все связанные данные успешно удалены!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    from sqlalchemy import and_
    
    import sys
    if len(sys.argv) >= 2:
        if '--id' in sys.argv:
            idx = sys.argv.index('--id')
            tournament_id = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else None
            delete_tournament_force(tournament_id=tournament_id)
        elif '--name' in sys.argv and '--date' in sys.argv:
            name_idx = sys.argv.index('--name')
            date_idx = sys.argv.index('--date')
            name = sys.argv[name_idx + 1] if name_idx + 1 < len(sys.argv) else None
            date = sys.argv[date_idx + 1] if date_idx + 1 < len(sys.argv) else None
            delete_tournament_force(tournament_name=name, tournament_date=date)
        else:
            print("Использование:")
            print("  python delete_tournament_force.py --id <tournament_id>")
            print("  python delete_tournament_force.py --name 'Название' --date 'DD.MM.YYYY'")
    else:
        # Интерактивный режим
        print("Введите данные для удаления турнира:")
        name = input("Название турнира (или Enter для пропуска): ").strip() or None
        date = input("Дата турнира (DD.MM.YYYY или Enter для пропуска): ").strip() or None
        tid = input("ID турнира (или Enter для пропуска): ").strip()
        tid = int(tid) if tid else None
        
        delete_tournament_force(tournament_name=name, tournament_date=date, tournament_id=tid)


