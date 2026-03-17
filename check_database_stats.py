# check_database_stats.py
"""
Скрипт для проверки статистики базы данных
"""

from database import SessionLocal
from models import User, Tournament, Registration, RegistrationStatus
from datetime import datetime

def check_database_stats():
    """Проверяет статистику базы данных"""
    session = SessionLocal()
    
    try:
        print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("=" * 40)
        
        # Пользователи
        users_count = session.query(User).count()
        print(f"👥 Пользователей (судьи): {users_count}")
        
        # Турниры
        tournaments_count = session.query(Tournament).count()
        print(f"🏆 Турниров: {tournaments_count}")
        
        # Заявки
        registrations_count = session.query(Registration).count()
        print(f"📝 Заявок: {registrations_count}")
        
        # Статистика по статусам заявок
        approved_count = session.query(Registration).filter(Registration.status == RegistrationStatus.APPROVED).count()
        rejected_count = session.query(Registration).filter(Registration.status == RegistrationStatus.REJECTED).count()
        pending_count = session.query(Registration).filter(Registration.status == RegistrationStatus.PENDING).count()
        
        print(f"\n📈 Статистика заявок:")
        print(f"  ✅ Утверждено: {approved_count}")
        print(f"  ❌ Отклонено: {rejected_count}")
        print(f"  ⏳ Ожидает: {pending_count}")
        
        # Даты турниров
        if tournaments_count > 0:
            first_tournament = session.query(Tournament).order_by(Tournament.date.asc()).first()
            last_tournament = session.query(Tournament).order_by(Tournament.date.desc()).first()
            
            print(f"\n📅 Период турниров:")
            print(f"  🗓️ Первый турнир: {first_tournament.date.strftime('%d.%m.%Y')} - {first_tournament.name}")
            print(f"  🗓️ Последний турнир: {last_tournament.date.strftime('%d.%m.%Y')} - {last_tournament.name}")
        
        # Топ-5 самых активных судей
        print(f"\n🏆 ТОП-5 САМЫХ АКТИВНЫХ СУДЕЙ:")
        from sqlalchemy import func
        top_judges = session.query(
            User.first_name, 
            User.last_name, 
            func.count(Registration.registration_id).label('registrations_count')
        ).join(Registration).group_by(User.user_id).order_by(func.count(Registration.registration_id).desc()).limit(5).all()
        
        for i, (first_name, last_name, count) in enumerate(top_judges, 1):
            print(f"  {i}. {first_name} {last_name} - {count} заявок")
        
        print("\n" + "=" * 40)
        
    except Exception as e:
        print(f"❌ Ошибка при проверке статистики: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database_stats()
