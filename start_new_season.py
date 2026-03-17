# start_new_season.py
"""
Безопасный скрипт для начала нового сезона
Создает резервную копию и подготавливает базу для нового сезона
"""

import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, Tournament, Registration
from database import SessionLocal

def create_backup():
    """Создает резервную копию текущей базы"""
    current_db = "bot_database.db"
    if not os.path.exists(current_db):
        print("❌ База данных не найдена!")
        return None
    
    backup_name = f"bot_database_season_2024_2025_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(current_db, backup_name)
    print(f"✅ Резервная копия создана: {backup_name}")
    return backup_name

def clear_tournaments_and_registrations():
    """Очищает турниры и заявки, оставляя пользователей"""
    session = SessionLocal()
    
    try:
        # Получаем статистику до очистки
        users_count = session.query(User).count()
        tournaments_count = session.query(Tournament).count()
        registrations_count = session.query(Registration).count()
        
        print(f"📊 Текущая статистика:")
        print(f"  👥 Пользователей: {users_count}")
        print(f"  🏆 Турниров: {tournaments_count}")
        print(f"  📝 Заявок: {registrations_count}")
        
        # Очищаем заявки
        deleted_registrations = session.query(Registration).delete()
        print(f"🗑️ Удалено заявок: {deleted_registrations}")
        
        # Очищаем турниры
        deleted_tournaments = session.query(Tournament).delete()
        print(f"🗑️ Удалено турниров: {deleted_tournaments}")
        
        # Сбрасываем автоинкремент для турниров
        session.execute(text("DELETE FROM sqlite_sequence WHERE name='tournament'"))
        session.execute(text("DELETE FROM sqlite_sequence WHERE name='registration'"))
        
        session.commit()
        
        print(f"\n✅ База данных очищена для нового сезона!")
        print(f"👥 Пользователей сохранено: {users_count}")
        print(f"🏆 Турниров: 0")
        print(f"📝 Заявок: 0")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def add_welcome_tournament():
    """Добавляет приветственный турнир для нового сезона"""
    session = SessionLocal()
    
    try:
        # Создаем приветственный турнир
        welcome_tournament = Tournament(
            name="🎉 Добро пожаловать в новый сезон 2025-2026!",
            date=datetime(2025, 9, 1).date(),
            month="Сентябрь"
        )
        
        session.add(welcome_tournament)
        session.commit()
        
        print(f"✅ Добавлен приветственный турнир: {welcome_tournament.name}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении приветственного турнира: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Основная функция"""
    print("🎉 НАЧАЛО НОВОГО СЕЗОНА 2025-2026")
    print("=" * 50)
    
    # Подтверждение
    print("\n⚠️  ВНИМАНИЕ!")
    print("Этот скрипт:")
    print("✅ Создаст резервную копию текущей базы")
    print("✅ Сохранит всех пользователей (судьи)")
    print("❌ Удалит ВСЕ турниры и заявки")
    print("✅ Добавит приветственный турнир")
    
    confirm = input("\nПродолжить? (да/нет): ").lower().strip()
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        return
    
    # 1. Создаем резервную копию
    print("\n1️⃣ Создание резервной копии...")
    backup_file = create_backup()
    if not backup_file:
        return
    
    # 2. Очищаем турниры и заявки
    print("\n2️⃣ Очистка базы данных...")
    if not clear_tournaments_and_registrations():
        return
    
    # 3. Добавляем приветственный турнир
    print("\n3️⃣ Добавление приветственного турнира...")
    add_welcome_tournament()
    
    print("\n" + "=" * 50)
    print("🎉 НОВЫЙ СЕЗОН 2025-2026 ГОТОВ!")
    print(f"📁 Резервная копия: {backup_file}")
    print("\n📋 Что было сделано:")
    print("✅ Создана резервная копия сезона 2024-2025")
    print("✅ Сохранены все пользователи (судьи)")
    print("✅ Удалены все турниры и заявки")
    print("✅ Добавлен приветственный турнир")
    print("✅ База готова для нового сезона")
    print("\n🚀 Теперь можно добавлять турниры нового сезона!")

if __name__ == "__main__":
    main()
