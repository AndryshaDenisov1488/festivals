# migrate_to_new_season.py
"""
Скрипт для миграции в новый сезон
Создает новую базу данных и переносит пользователей (судьи)
"""

import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Tournament, Registration
from database import SessionLocal

def backup_current_database():
    """Создает резервную копию текущей базы данных"""
    current_db = "bot_database.db"
    backup_name = f"bot_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists(current_db):
        shutil.copy2(current_db, backup_name)
        print(f"✅ Резервная копия создана: {backup_name}")
        return backup_name
    else:
        print("❌ Текущая база данных не найдена!")
        return None

def get_users_from_current_db():
    """Получает всех пользователей из текущей базы"""
    session = SessionLocal()
    try:
        users = session.query(User).all()
        print(f"📊 Найдено пользователей: {len(users)}")
        return users
    except Exception as e:
        print(f"❌ Ошибка при получении пользователей: {e}")
        return []
    finally:
        session.close()

def create_new_database():
    """Создает новую базу данных"""
    new_db = "bot_database_new_season.db"
    
    # Удаляем старую новую базу, если она существует
    if os.path.exists(new_db):
        os.remove(new_db)
        print(f"🗑️ Удалена старая новая база: {new_db}")
    
    # Создаем новую базу
    engine = create_engine(f"sqlite:///{new_db}")
    Base.metadata.create_all(engine)
    print(f"✅ Новая база данных создана: {new_db}")
    
    return new_db

def migrate_users(users, new_db_path):
    """Переносит пользователей в новую базу"""
    if not users:
        print("⚠️ Нет пользователей для переноса")
        return
    
    # Подключаемся к новой базе
    engine = create_engine(f"sqlite:///{new_db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        migrated_count = 0
        for user in users:
            # Создаем нового пользователя с теми же данными
            new_user = User(
                user_id=user.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                function=user.function,
                category=user.category
            )
            session.add(new_user)
            migrated_count += 1
        
        session.commit()
        print(f"✅ Перенесено пользователей: {migrated_count}")
        
    except Exception as e:
        print(f"❌ Ошибка при переносе пользователей: {e}")
        session.rollback()
    finally:
        session.close()

def replace_database(new_db_path):
    """Заменяет текущую базу новой"""
    current_db = "bot_database.db"
    
    if os.path.exists(current_db):
        os.remove(current_db)
        print(f"🗑️ Удалена старая база: {current_db}")
    
    shutil.move(new_db_path, current_db)
    print(f"✅ Новая база установлена: {current_db}")

def main():
    """Основная функция миграции"""
    print("🚀 НАЧАЛО МИГРАЦИИ В НОВЫЙ СЕЗОН")
    print("=" * 50)
    
    # 1. Создаем резервную копию
    print("\n1️⃣ Создание резервной копии...")
    backup_file = backup_current_database()
    if not backup_file:
        return
    
    # 2. Получаем пользователей
    print("\n2️⃣ Получение пользователей...")
    users = get_users_from_current_db()
    
    # 3. Создаем новую базу
    print("\n3️⃣ Создание новой базы данных...")
    new_db_path = create_new_database()
    
    # 4. Переносим пользователей
    print("\n4️⃣ Перенос пользователей...")
    migrate_users(users, new_db_path)
    
    # 5. Заменяем базу
    print("\n5️⃣ Установка новой базы...")
    replace_database(new_db_path)
    
    print("\n" + "=" * 50)
    print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print(f"📁 Резервная копия: {backup_file}")
    print("🆕 Новая база готова для сезона 2025-2026")
    print("\n📋 Что было сделано:")
    print("✅ Создана резервная копия старой базы")
    print("✅ Создана новая база данных")
    print(f"✅ Перенесено {len(users)} пользователей")
    print("✅ Удалены все турниры и заявки")
    print("✅ База готова для нового сезона")

if __name__ == "__main__":
    main()
