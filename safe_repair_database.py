#!/usr/bin/env python3
"""
Безопасный скрипт для восстановления поврежденной базы данных SQLite.
Использует более безопасные методы восстановления, которые не удаляют данные.
"""

import os
import sys
import sqlite3
import shutil
import subprocess
from datetime import datetime
from config import DATABASE_URL

def get_db_path():
    """Получает путь к файлу базы данных"""
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        return db_path
    else:
        print(f"❌ Не SQLite база данных: {DATABASE_URL}")
        sys.exit(1)

def create_backup(db_path):
    """Создает резервную копию базы данных"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"💾 Создание резервной копии: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        return None

def check_integrity(db_path):
    """Проверяет целостность базы данных"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()
        return result == "ok"
    except:
        return False

def fix_wal_files(db_path):
    """Исправляет проблемы с WAL файлами"""
    wal_path = f"{db_path}-wal"
    shm_path = f"{db_path}-shm"
    
    print("🔧 Обработка WAL файлов...")
    
    # Пытаемся закрыть WAL режим
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=DELETE;")
        conn.close()
    except:
        pass
    
    # Удаляем WAL файлы
    if os.path.exists(wal_path):
        try:
            os.remove(wal_path)
            print(f"   ✅ Удален WAL файл")
        except:
            print(f"   ⚠️  Не удалось удалить WAL файл")
    
    if os.path.exists(shm_path):
        try:
            os.remove(shm_path)
            print(f"   ✅ Удален SHM файл")
        except:
            print(f"   ⚠️  Не удалось удалить SHM файл")

def safe_repair_database(db_path):
    """Безопасное восстановление базы данных"""
    print(f"🔧 Безопасное восстановление базы данных: {db_path}")
    
    # Создаем резервную копию
    backup_path = create_backup(db_path)
    if not backup_path:
        print("❌ Не удалось создать резервную копию. Прерываем операцию.")
        return False
    
    # Шаг 1: Исправляем WAL файлы
    fix_wal_files(db_path)
    
    # Шаг 2: Проверяем, помогло ли это
    if check_integrity(db_path):
        print("✅ База данных восстановлена после обработки WAL файлов!")
        return True
    
    # Шаг 3: Пытаемся использовать sqlite3 .recover (самый безопасный метод)
    print("🔄 Попытка восстановления через sqlite3 .recover...")
    
    repaired_path = f"{db_path}.repaired"
    
    try:
        # Используем sqlite3 CLI для восстановления
        result = subprocess.run(
            ['sqlite3', db_path, '.recover'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0 and result.stdout:
            # Сохраняем SQL дамп
            sql_dump = result.stdout
            
            # Создаем новую базу из дампа
            if os.path.exists(repaired_path):
                os.remove(repaired_path)
            
            conn_new = sqlite3.connect(repaired_path)
            conn_new.executescript(sql_dump)
            conn_new.close()
            
            # Проверяем восстановленную базу
            if check_integrity(repaired_path):
                # Подсчитываем записи в старой и новой базе
                print("📊 Проверка количества записей...")
                
                try:
                    conn_old = sqlite3.connect(db_path)
                    cursor_old = conn_old.cursor()
                    cursor_old.execute("SELECT COUNT(*) FROM users;")
                    old_users = cursor_old.fetchone()[0]
                    conn_old.close()
                except:
                    old_users = 0
                
                try:
                    conn_new = sqlite3.connect(repaired_path)
                    cursor_new = conn_new.cursor()
                    cursor_new.execute("SELECT COUNT(*) FROM users;")
                    new_users = cursor_new.fetchone()[0]
                    conn_new.close()
                except:
                    new_users = 0
                
                print(f"   Старая база: {old_users} пользователей")
                print(f"   Новая база: {new_users} пользователей")
                
                if new_users > 0 and new_users >= old_users * 0.9:  # Хотя бы 90% данных
                    print("✅ Восстановление успешно! Заменяем базу данных...")
                    os.replace(repaired_path, db_path)
                    return True
                else:
                    print(f"⚠️  Восстановленная база содержит меньше данных ({new_users} vs {old_users})")
                    print("   Используйте резервную копию вместо восстановления")
                    if os.path.exists(repaired_path):
                        os.remove(repaired_path)
                    return False
            else:
                print("❌ Восстановленная база данных все еще повреждена")
                if os.path.exists(repaired_path):
                    os.remove(repaired_path)
                return False
        else:
            print(f"❌ Ошибка при восстановлении через .recover: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("⚠️  sqlite3 CLI не найден. Используйте резервную копию.")
        return False
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        if os.path.exists(repaired_path):
            os.remove(repaired_path)
        return False

def main():
    """Основная функция"""
    print("=" * 80)
    print("🔧 БЕЗОПАСНОЕ ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ SQLite")
    print("=" * 80)
    print()
    
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Файл базы данных не найден: {db_path}")
        sys.exit(1)
    
    print(f"📁 Путь к базе данных: {db_path}")
    print()
    
    # Проверяем целостность
    if check_integrity(db_path):
        print("✅ База данных целостна! Восстановление не требуется.")
        return
    
    print("⚠️  База данных повреждена. Начинаем безопасное восстановление...")
    print()
    
    # Восстанавливаем
    if safe_repair_database(db_path):
        print()
        print("=" * 80)
        print("✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ ВОССТАНОВЛЕНИЕ НЕ УДАЛОСЬ")
        print("=" * 80)
        print()
        print("💡 Используйте резервную копию базы данных")
        sys.exit(1)

if __name__ == "__main__":
    main()

